from typing import List
from pydantic import BaseModel
import datetime as dt

class WeatherSummary(BaseModel):
    city: str
    dates: List[str]
    highs_c: List[float]
    lows_c: List[float]
    conditions: List[str]

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