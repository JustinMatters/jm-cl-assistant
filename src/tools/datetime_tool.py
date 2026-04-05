"""Date and time tool using the system clock and zoneinfo.

Returns the current date/time for the local system timezone by default.
When the user asks for a specific location (e.g. "what time is it in Tokyo?"),
the query is parsed for a city or IANA timezone name and the result is
adjusted accordingly.  No external dependencies required.
"""

from __future__ import annotations

import re
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.tools.registry import REGISTRY, ToolDefinition

# Common city / alias → IANA timezone name.
# Users can also supply an IANA name directly (e.g. "America/Chicago").
_CITY_TZ: dict[str, str] = {
    # Asia/Pacific
    "tokyo": "Asia/Tokyo",
    "osaka": "Asia/Tokyo",
    "seoul": "Asia/Seoul",
    "beijing": "Asia/Shanghai",
    "shanghai": "Asia/Shanghai",
    "hong kong": "Asia/Hong_Kong",
    "singapore": "Asia/Singapore",
    "bangkok": "Asia/Bangkok",
    "jakarta": "Asia/Jakarta",
    "sydney": "Australia/Sydney",
    "melbourne": "Australia/Melbourne",
    "brisbane": "Australia/Brisbane",
    "perth": "Australia/Perth",
    "auckland": "Pacific/Auckland",
    "honolulu": "Pacific/Honolulu",
    "hawaii": "Pacific/Honolulu",
    # South/West Asia
    "dubai": "Asia/Dubai",
    "abu dhabi": "Asia/Dubai",
    "riyadh": "Asia/Riyadh",
    "mumbai": "Asia/Kolkata",
    "delhi": "Asia/Kolkata",
    "kolkata": "Asia/Kolkata",
    "karachi": "Asia/Karachi",
    "dhaka": "Asia/Dhaka",
    "colombo": "Asia/Colombo",
    "tehran": "Asia/Tehran",
    # Europe
    "moscow": "Europe/Moscow",
    "istanbul": "Europe/Istanbul",
    "ankara": "Europe/Istanbul",
    "helsinki": "Europe/Helsinki",
    "stockholm": "Europe/Stockholm",
    "oslo": "Europe/Oslo",
    "copenhagen": "Europe/Copenhagen",
    "warsaw": "Europe/Warsaw",
    "kyiv": "Europe/Kyiv",
    "kiev": "Europe/Kyiv",
    "bucharest": "Europe/Bucharest",
    "budapest": "Europe/Budapest",
    "vienna": "Europe/Vienna",
    "zurich": "Europe/Zurich",
    "bern": "Europe/Zurich",
    "geneva": "Europe/Zurich",
    "prague": "Europe/Prague",
    "paris": "Europe/Paris",
    "berlin": "Europe/Berlin",
    "brussels": "Europe/Brussels",
    "amsterdam": "Europe/Amsterdam",
    "rome": "Europe/Rome",
    "milan": "Europe/Rome",
    "madrid": "Europe/Madrid",
    "barcelona": "Europe/Madrid",
    "lisbon": "Europe/Lisbon",
    "london": "Europe/London",
    "edinburgh": "Europe/London",
    "dublin": "Europe/Dublin",
    "reykjavik": "Atlantic/Reykjavik",
    # Africa
    "cairo": "Africa/Cairo",
    "johannesburg": "Africa/Johannesburg",
    "cape town": "Africa/Johannesburg",
    "nairobi": "Africa/Nairobi",
    "lagos": "Africa/Lagos",
    "accra": "Africa/Accra",
    "casablanca": "Africa/Casablanca",
    # Americas
    "new york": "America/New_York",
    "nyc": "America/New_York",
    "boston": "America/New_York",
    "miami": "America/New_York",
    "toronto": "America/Toronto",
    "montreal": "America/Toronto",
    "chicago": "America/Chicago",
    "dallas": "America/Chicago",
    "houston": "America/Chicago",
    "denver": "America/Denver",
    "phoenix": "America/Phoenix",
    "los angeles": "America/Los_Angeles",
    "la": "America/Los_Angeles",
    "san francisco": "America/Los_Angeles",
    "seattle": "America/Los_Angeles",
    "vancouver": "America/Vancouver",
    "mexico city": "America/Mexico_City",
    "bogota": "America/Bogota",
    "lima": "America/Lima",
    "santiago": "America/Santiago",
    "sao paulo": "America/Sao_Paulo",
    "buenos aires": "America/Argentina/Buenos_Aires",
    # UTC / aliases
    "utc": "UTC",
    "gmt": "UTC",
}

# Pattern to extract an "in <location>" clause from the query.
_IN_LOCATION = re.compile(
    r"\bin\s+([a-zA-Z][a-zA-Z\s/_.+-]{1,40})\s*[?.]?\s*$",
    re.IGNORECASE,
)


def _resolve_timezone(location: str) -> ZoneInfo | None:
    """Attempt to resolve a location string to a ZoneInfo object.

    Tries the city lookup table first, then attempts to use the string
    directly as an IANA timezone name.

    Args:
        location: City name or IANA timezone string, e.g. ``"Tokyo"``
          or ``"America/Chicago"``.

    Returns:
        A ``ZoneInfo`` instance, or ``None`` if not recognised.
    """
    key = location.strip().lower()
    iana = _CITY_TZ.get(key)
    if iana is None:
        iana = location.strip()
    try:
        return ZoneInfo(iana)
    except (ZoneInfoNotFoundError, KeyError):
        return None


def _format_dt(dt: datetime) -> str:
    """Format a datetime as a human-readable string.

    Uses cross-platform formatting — avoids ``%-d`` (Linux-only) by
    stripping the leading zero from the day field manually.

    Args:
        dt: A timezone-aware datetime object.

    Returns:
        A string like ``"Sunday 5 April 2026, 14:35 BST"``.
    """
    day = str(dt.day)
    return dt.strftime(f"%A {day} %B %Y, %H:%M %Z").strip()


def get_datetime(timezone: str | None = None) -> str:
    """Return the current date and time as a formatted string.

    Args:
        timezone: Optional IANA timezone name or common city name.
          When ``None``, the system's local timezone is used.

    Returns:
        A formatted string such as ``"Sunday 5 April 2026, 14:35 BST"``
        (local time) or ``"Sunday 5 April 2026, 22:35 JST (Asia/Tokyo)"``
        (named timezone).
    """
    if timezone:
        tz = _resolve_timezone(timezone)
        if tz is None:
            utc_str = _format_dt(datetime.now(ZoneInfo("UTC")))
            return f"Unknown timezone {timezone!r}. Showing UTC: {utc_str}"
        now = datetime.now(tz)
        return f"{_format_dt(now)} ({tz.key})"

    now = datetime.now().astimezone()
    return _format_dt(now)


def _handle_datetime_query(query: str) -> str:
    """Handle a raw datetime query, detecting an optional location.

    Checks for an "in <location>" clause and passes the location to
    ``get_datetime`` for timezone conversion.

    Args:
        query: The raw user query string.

    Returns:
        A formatted date/time string.
    """
    match = _IN_LOCATION.search(query)
    if match:
        return get_datetime(timezone=match.group(1).strip())
    return get_datetime()


REGISTRY.register(
    ToolDefinition(
        name="datetime",
        router_tier="datetime",
        label="Tool: date/time",
        description=(
            "queries about the current date, time, day, or year — "
            "locally or for a specific city or timezone"
        ),
        examples=[
            "what time is it",
            "what is today's date",
            "what day is it",
            "what time is it in Tokyo",
            "what's the time in New York",
        ],
        default_enabled=True,
        min_tier="trivial_ollama",
        approach="A",
        callable=_handle_datetime_query,
        category="time",
    )
)
