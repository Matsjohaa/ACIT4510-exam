"""Download historical Oslo weather from Open-Meteo for comparison with Oslo Bysykkel trips.

Outputs (in data/weather/):
  - oslo_weather_hourly.csv: one row per hour, `time` in UTC (same as bysykkel `started_at`).
    Join with: trips["hour"] = pd.to_datetime(trips["started_at"], format="ISO8601").dt.floor("h")
  - oslo_weather_daily.csv: one row per local (Europe/Oslo) calendar day, `date` column.
"""

import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

LATITUDE = 59.9139  # Oslo city centre
LONGITUDE = 10.7522
START_DATE = "2025-01-01"
END_DATE = "2025-12-31"

API_URL = "https://archive-api.open-meteo.com/v1/archive"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "weather"

HOURLY_VARIABLES = [
    "temperature_2m",        # °C
    "relative_humidity_2m",  # %
    "precipitation",         # mm (rain + snow water equivalent)
    "rain",                  # mm
    "snowfall",              # cm
    "snow_depth",            # m
    "cloud_cover",           # %
    "sunshine_duration",     # s within the hour
    "wind_speed_10m",        # m/s
    "wind_gusts_10m",        # m/s
    "weather_code",          # WMO code
]

DAILY_VARIABLES = [
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "relative_humidity_2m_mean",
    "precipitation_sum",
    "rain_sum",
    "snowfall_sum",
    "precipitation_hours",
    "cloud_cover_mean",
    "sunshine_duration",
    "daylight_duration",
    "wind_speed_10m_mean",
    "wind_gusts_10m_max",
    "weather_code",
]


def fetch(frequency: str, variables: list[str], timezone: str) -> pd.DataFrame:
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": START_DATE,
        "end_date": END_DATE,
        frequency: ",".join(variables),
        "timezone": timezone,
        "wind_speed_unit": "ms",
    }
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.load(response)
    return pd.DataFrame(data[frequency])


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    hourly = fetch("hourly", HOURLY_VARIABLES, timezone="UTC")
    hourly["time"] = pd.to_datetime(hourly["time"]).dt.tz_localize("UTC")
    hourly["weather_code"] = hourly["weather_code"].astype("Int64")
    hourly.to_csv(OUTPUT_DIR / "oslo_weather_hourly.csv", index=False)

    daily = fetch("daily", DAILY_VARIABLES, timezone="Europe/Oslo")
    daily = daily.rename(columns={"time": "date"})
    daily["date"] = pd.to_datetime(daily["date"]).dt.date
    daily["weather_code"] = daily["weather_code"].astype("Int64")
    # Seconds -> hours for readability
    daily["sunshine_duration"] = daily["sunshine_duration"] / 3600
    daily["daylight_duration"] = daily["daylight_duration"] / 3600
    daily.to_csv(OUTPUT_DIR / "oslo_weather_daily.csv", index=False)

    print(f"Saved {len(hourly)} hourly rows and {len(daily)} daily rows to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
