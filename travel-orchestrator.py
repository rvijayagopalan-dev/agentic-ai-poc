import os
import asyncio
import json
from typing import Any, Dict
from dotenv import load_dotenv
from openai import OpenAI

from travel_domain_agents import (
    weather_agent, flights_agent, hotels_agent,
    events_agent, book_agent, TravelerPrefs, Itinerary,
    FlightOption, HotelOption, TOOLS
)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


# =========================
# Orchestrator
# =========================
class TravelOrchestrator:
    """
    A loop that:
      1) sends user goal/context to GPT-5 with tool schemas
      2) executes requested tools
      3) feeds results back until GPT outputs a final structured itinerary
    """

    def __init__(self):
        self.accumulator: Dict[str, Any] = {
            "weather": None,
            "flights": [],
            "hotels": [],
            "events": [],
            "booking": None,
        }

    async def run(self, user_goal: str, default_prefs: TravelerPrefs, auto_book: bool = False) -> Itinerary:
        sys = (
            "You are a senior travel-planning orchestrator. "
            "Plan minimal tool calls, prefer parallelizable requests, and return a cohesive itinerary. "
            "When making a plan: summarize, list chosen flight/hotel, include weather overview, key events, "
            "and a day-by-day schedule. Keep budgets in the user's currency."
        )

        messages = [
            {"role": "system", "content": sys},
            {
                "role": "user",
                "content": json.dumps({
                    "goal": user_goal,
                    "defaults": default_prefs.dict(),
                    "notes": "Use tools to fetch facts; then produce a final structured itinerary JSON matching the Itinerary schema."
                })
            },
        ]

        async def handle_tool(tool_name: str, args: Dict[str, Any]):
            if tool_name == "call_weather_agent":
                res = await weather_agent(**args)
                self.accumulator["weather"] = res.dict()
                return json.dumps(self.accumulator["weather"])

            if tool_name == "call_flights_agent":
                prefs = TravelerPrefs(**args["prefs"])
                res = await flights_agent(prefs)
                self.accumulator["flights"] = [r.dict() for r in res]
                return json.dumps(self.accumulator["flights"])

            if tool_name == "call_hotels_agent":
                res = await hotels_agent(**args)
                self.accumulator["hotels"] = [r.dict() for r in res]
                return json.dumps(self.accumulator["hotels"])

            if tool_name == "call_events_agent":
                res = await events_agent(**args)
                self.accumulator["events"] = [r.dict() for r in res]
                return json.dumps(self.accumulator["events"])

            if tool_name == "finalize_booking":
                flights = self.accumulator.get("flights", [])
                hotels = self.accumulator.get("hotels", [])
                fi = int(args["flight_index"])
                hi = int(args.get("hotel_index", 0))
                selected_flight = FlightOption(**flights[fi])
                selected_hotel = HotelOption(**hotels[hi]) if hotels else None
                res = await book_agent(selected_flight, selected_hotel)
                self.accumulator["booking"] = res
                return json.dumps(res)

            raise ValueError(f"Unknown tool: {tool_name}")

        for _ in range(8):  # hard cap to avoid infinite loops
            resp = client.chat.completions.create(
                model="gpt-5",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0.2,
            )
            choice = resp.choices[0]
            msg = choice.message

            if not getattr(msg, "tool_calls", None):
                try:
                    data = json.loads(msg.content)
                    return Itinerary(**data)
                except Exception:
                    messages.append({"role": "assistant", "content": msg.content})
                    messages.append({
                        "role": "user",
                        "content": "Please output valid JSON strictly matching the Itinerary schema."
                    })
                    continue

            results: Dict[str, str] = {}
            pending = []
            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments or "{}")
                pending.append((name, args))

            async def _run_all():
                async def _one(n, a):
                    return n, await handle_tool(n, a)
                return await asyncio.gather(*[_one(n, a) for n, a in pending])

            outs = await _run_all()
            for n, o in outs:
                results[n] = o

            for tc in msg.tool_calls:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": tc.function.name,
                    "content": results[tc.function.name],
                })

        raise RuntimeError("Failed to produce itinerary in allotted steps")

# =========================
# Example Usage
# =========================
async def example():
    prefs = TravelerPrefs(
        origin="SFO",
        destination="Vancouver",
        depart_date="2025-10-10",
        return_date="2025-10-14",
        travelers=2,
        cabin="economy",
        budget_currency="USD",
        max_flight_price=1200,
        max_hotel_price_per_night=250,
        hotel_rooms=1,
        interests=["food", "music", "outdoors"]
    )

    user_goal = (
        "Plan a 4-day fall getaway to Vancouver for two adults. "
        "Keep flights under $1200 total if possible, walkable hotel near food spots, "
        "include at least one live music event and a scenic day trip. Provide a clear daily plan. "
        "If options look good, go ahead and book the best value flight and hotel."
    )

    orchestrator = TravelOrchestrator()
    itinerary = await orchestrator.run(user_goal=user_goal, default_prefs=prefs, auto_book=True)

    print("\n=== Final Itinerary ===")
    print(json.dumps(itinerary.dict(), indent=2))

if __name__ == "__main__":
    asyncio.run(example())