import requests
import datetime as dt
from typing import List
from pydantic import BaseModel

class WeatherSummary(BaseModel):
    city: str
    dates: List[str]
    highs_c: List[float]
    lows_c: List[float]
    conditions: List[str]

async def weather_agent(city: str, start_date: str, end_date: str) -> WeatherSummary:
    api_key = "your_api_key_here"  # Replace with your actual Visual Crossing API key
    url = f"https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/{city}/{start_date}/{end_date}"

    params = {
        "unitGroup": "metric",
        "contentType": "json",
        "key": api_key
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception(f"Error fetching data: {response.status_code} - {response.text}")

    data = response.json()
    days = data.get("days", [])

    return WeatherSummary(
        city=city,
        dates=[day["datetime"] for day in days],
        highs_c=[day["tempmax"] for day in days],
        lows_c=[day["tempmin"] for day in days],
        conditions=[day["conditions"] for day in days]
    )