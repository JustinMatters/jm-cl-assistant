"""Weather forecast tool using the Open-Meteo API (no key required).

Fetches a day-by-day forecast using Open-Meteo's free forecast and
geocoding endpoints.  Location names are resolved to coordinates via the
Open-Meteo geocoding API.  When location is ``"auto"``, the user's IP
geolocation (T19.11) is used instead.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
import urllib.request
from datetime import date

from src.tools.location import get_location
from src.tools.registry import REGISTRY, ToolDefinition

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes → human-readable label
_WMO: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Icy fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light showers",
    81: "Showers",
    82: "Heavy showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}

# Pattern to extract location from query
_LOCATION_RE = re.compile(
    r"(?:weather|forecast)\s+"
    r"(?:in|for|at|near)\s+"
    r"([a-zA-Z][a-zA-Z\s,.-]{1,50}?)"
    r"(?:\s*[?.]|\s*$)",
    re.IGNORECASE,
)


def _geocode(location: str) -> tuple[float, float, str] | None:
    """Resolve a location name to (lat, lon, display_name).

    Args:
        location: A city or place name, e.g. ``"London"``.

    Returns:
        A ``(latitude, longitude, display_name)`` tuple, or ``None``
        if the location could not be resolved.
    """
    params = urllib.parse.urlencode(
        {"name": location, "count": 1, "language": "en", "format": "json"}
    )
    url = f"{_GEOCODE_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        logging.warning("Geocoding request failed: %s", exc)
        return None

    results = data.get("results")
    if not results:
        return None

    r = results[0]
    name = r.get("name", location)
    country = r.get("country", "")
    display = f"{name}, {country}".strip(", ")
    return r["latitude"], r["longitude"], display


def get_weather(location: str = "auto", days: int = 7) -> str:
    """Fetch a day-by-day weather forecast.

    Args:
        location: City name, or ``"auto"`` to use IP geolocation.
        days: Number of forecast days (1–7).

    Returns:
        A plain-text day-by-day forecast, or an error message.
    """
    days = max(1, min(days, 7))

    # Resolve coordinates
    if location.lower() == "auto":
        loc = get_location()
        if "error" in loc:
            return f"Could not determine location: {loc['error']}"
        lat = loc["lat"]
        lon = loc["lon"]
        city = loc.get("city") or loc.get("country") or "your location"
        display = city
    else:
        result = _geocode(location)
        if result is None:
            return f"Could not find location: {location!r}"
        lat, lon, display = result

    # Fetch forecast
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "daily": (
                "weathercode,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "precipitation_probability_max"
            ),
            "timezone": "auto",
            "forecast_days": days,
        }
    )
    url = f"{_FORECAST_URL}?{params}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        return f"(Weather API error: {exc})"

    daily = data.get("daily", {})
    dates = daily.get("time", [])
    codes = daily.get("weathercode", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_probability_max", [])

    if not dates:
        return "No forecast data available."

    lines = [f"Weather forecast for {display}:"]
    for i, day_str in enumerate(dates):
        day = date.fromisoformat(day_str)
        label = day.strftime(f"%A {day.day} %b")
        condition = (
            _WMO.get(int(codes[i]), "Unknown") if i < len(codes) else "—"
        )
        hi = (
            f"{highs[i]:.0f}°C"
            if i < len(highs) and highs[i] is not None
            else "—"
        )
        lo = (
            f"{lows[i]:.0f}°C" if i < len(lows) and lows[i] is not None else "—"
        )
        rain = (
            f"{int(precip[i])}% rain"
            if i < len(precip) and precip[i] is not None
            else ""
        )
        parts = [f"{label}: {condition}, {hi}/{lo}"]
        if rain:
            parts.append(rain)
        lines.append("  " + ", ".join(parts))

    return "\n".join(lines)


def _handle_weather_query(query: str) -> str:
    """Handle a raw weather query, extracting location if present.

    Args:
        query: The raw user query string.

    Returns:
        A plain-text weather forecast string.
    """
    match = _LOCATION_RE.search(query)
    location = match.group(1).strip() if match else "auto"
    return get_weather(location=location)


REGISTRY.register(
    ToolDefinition(
        name="weather",
        router_tier="weather",
        label="Tool: weather",
        description=(
            "queries about current or upcoming weather, temperature, "
            "rain, or forecast for a location"
        ),
        examples=[
            "what's the weather in London",
            "weather forecast for Tokyo",
            "will it rain tomorrow",
            "what is the weather today",
        ],
        default_enabled=True,
        min_tier="trivial_ollama",
        approach="A",
        callable=_handle_weather_query,
        category="web",
    )
)
