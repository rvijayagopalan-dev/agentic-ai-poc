import os
import json
import asyncio
import datetime as dt
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, validator
import httpx
from openai import OpenAI

# =========================
# Config
# =========================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Please set OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# =========================
# Pydantic Schemas
# =========================
class WeatherSummary(BaseModel):
    city: str
    dates: List[str]
    highs_c: List[float]
    lows_c: List[float]
    conditions: List[str]
class FlightOption(BaseModel):
    carrier: str
    flight_number: str
    depart_time_local: str
    arrive_time_local: str
    duration: str
    cabin: Literal["economy", "premium_economy", "business", "first"]
    price_currency: str
    price_total: float
class HotelOption(BaseModel):
    name: str
    address: str
    checkin: str
    checkout: str
    rating: float
    price_currency: str
    price_total: float
    cancellation_policy: Optional[str] = None
class EventOption(BaseModel):
    title: str
    start: str
    end: Optional[str] = None
    venue: Optional[str] = None
    price_currency: Optional[str] = None
    price_total: Optional[float] = None
    category: Optional[str] = None
    url: Optional[str] = None
class TravelerPrefs(BaseModel):
    origin: str
    destination: str
    depart_date: str
    return_date: Optional[str]
    travelers: int = 1
    cabin: Literal["economy", "premium_economy", "business", "first"] = "economy"
    budget_currency: str = "USD"
    max_flight_price: Optional[float] = None
    max_hotel_price_per_night: Optional[float] = None
    hotel_rooms: int = 1
    interests: List[str] = Field(default_factory=list)
    @validator("depart_date", "return_date", pre=True, always=True)
    def _check_date(cls, v):
        if v is None:
            return v
        dt.date.fromisoformat(v)  # raises if invalid
        return v
class ItineraryDay(BaseModel):
    date: str
    morning: Optional[str] = None
    afternoon: Optional[str] = None
    evening: Optional[str] = None
    notes: Optional[str] = None
class Itinerary(BaseModel):
    summary: str
    flights: List[FlightOption]
    hotel: Optional[HotelOption]
    weather: Optional[WeatherSummary]
    events: List[EventOption] = Field(default_factory=list)
    plan: List[ItineraryDay] = Field(default_factory=list)
    est_total_currency: str
    est_total_amount: float

# =========================
# Domain Agent Stubs (replace with real APIs)
# =========================
async def weather_agent(city: str, start_date: str, end_date: str) -> WeatherSummary:
    # TODO: Replace with OpenWeather/VisualCrossing/etc.
    start = dt.date.fromisoformat(start_date)
    end = dt.date.fromisoformat(end_date)
    days = (end - start).days + 1
    highs = [26.0 + i % 3 for i in range(days)]
    lows  = [18.0 + i % 3 for i in range(days)]
    conds = ["clear", "partly cloudy", "light rain"] * ((days // 3) + 1)
    return WeatherSummary(
        city=city,
        dates=[(start + dt.timedelta(days=i)).isoformat() for i in range(days)],
        highs_c=highs[:days],
        lows_c=lows[:days],
        conditions=conds[:days],
    )
async def flights_agent(prefs: TravelerPrefs) -> List[FlightOption]:
    # TODO: Replace with Amadeus/Skyscanner/Sabre/etc.
    return [
        FlightOption(
            carrier="Example Air",
            flight_number="EA123",
            depart_time_local=f"{prefs.depart_date}T09:15",
            arrive_time_local=f"{prefs.depart_date}T14:45",
            duration="5h 30m",
            cabin=prefs.cabin,
            price_currency=prefs.budget_currency,
            price_total=480.0 * prefs.travelers,
        ),
        FlightOption(
            carrier="SampleJet",
            flight_number="SJ456",
            depart_time_local=f"{prefs.depart_date}T17:30",
            arrive_time_local=f"{prefs.depart_date}T23:05",
            duration="5h 35m",
            cabin=prefs.cabin,
            price_currency=prefs.budget_currency,
            price_total=520.0 * prefs.travelers,
        ),
    ]
async def hotels_agent(destination: str, checkin: str, checkout: str, rooms: int, max_price_per_night: Optional[float], currency: str) -> List[HotelOption]:
    # TODO: Replace with Booking.com/Hotels.com/Expedia API, etc.
    nights = (dt.date.fromisoformat(checkin) - dt.date.fromisoformat(checkout)).days
    nights = abs(nights) or 1
    base = 140.0
    total = base * nights * rooms
    return [
        HotelOption(
            name="Central Square Hotel",
            address=f"Downtown, {destination}",
            checkin=checkin,
            checkout=checkout,
            rating=4.5,
            price_currency=currency,
            price_total=total,
            cancellation_policy="Free cancellation until 24h before check-in",
        ),
        HotelOption(
            name="Riverside Boutique",
            address=f"Riverside, {destination}",
            checkin=checkin,
            checkout=checkout,
            rating=4.2,
            price_currency=currency,
            price_total=total * 1.1,
            cancellation_policy="Partial refund",
        ),
    ]
async def events_agent(city: str, start_date: str, end_date: str, interests: List[str]) -> List[EventOption]:
    # TODO: Replace with Eventbrite/Ticketmaster/Local event APIs.
    return [
        EventOption(
            title="Open-Air Food Market",
            start=f"{start_date}T18:00",
            end=f"{start_date}T21:00",
            venue="Old Town Plaza",
            category="food",
            price_currency="USD",
            price_total=0.0,
            url="https://example.com/events/market",
        ),
        EventOption(
            title="Live Jazz Night",
            start=f"{(dt.date.fromisoformat(start_date) + dt.timedelta(days=1)).isoformat()}T20:00",
            venue="Blue Note Club",
            category="music",
            price_currency="USD",
            price_total=35.0,
            url="https://example.com/events/jazz",
        ),
    ]

async def book_agent(selected_flight: FlightOption, selected_hotel: Optional[HotelOption]) -> Dict[str, Any]:
    # TODO: Replace with your real booking flows (payments, PNR, vouchers)
    return {
        "flight_booking_id": "BK-FLT-XYZ123",
        "hotel_booking_id": "BK-HTL-ABC987" if selected_hotel else None,
        "status": "PENDING_CONFIRMATION"
    }
# =========================
# Tool / Function metadata for GPT-5
# =========================
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "call_weather_agent",
            "description": "Get a short-term weather summary for a city and date range",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                },
                "required": ["city", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_flights_agent",
            "description": "Search flight options based on traveler preferences",
            "parameters": {
                "type": "object",
                "properties": {
                    "prefs": {
                        "type": "object",
                        "description": "Traveler preferences",
                        "properties": {
                            "origin": {"type": "string"},
                            "destination": {"type": "string"},
                            "depart_date": {"type": "string"},
                            "return_date": {"type": "string"},
                            "travelers": {"type": "number"},
                            "cabin": {"type": "string"},
                            "budget_currency": {"type": "string"},
                            "max_flight_price": {"type": "number"},
                        },
                        "required": ["origin", "destination", "depart_date", "travelers", "cabin", "budget_currency"],
                    }
                },
                "required": ["prefs"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_hotels_agent",
            "description": "Search hotel options",
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string"},
                    "checkin": {"type": "string"},
                    "checkout": {"type": "string"},
                    "rooms": {"type": "number"},
                    "max_price_per_night": {"type": "number"},
                    "currency": {"type": "string"},
                },
                "required": ["destination", "checkin", "checkout", "rooms", "currency"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "call_events_agent",
            "description": "Search local events matching user interests",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "interests": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["city", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "finalize_booking",
            "description": "Attempt to book selected flight and hotel",
            "parameters": {
                "type": "object",
                "properties": {
                    "flight_index": {"type": "number"},
                    "hotel_index": {"type": "number"},
                },
                "required": ["flight_index"],
            },
        },
    },
]
