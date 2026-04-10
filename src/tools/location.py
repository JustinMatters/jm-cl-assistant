"""Location tool using IP geolocation via ip-api.com.

Resolves the user's approximate location from their public IP address.
The result is cached for the session to avoid repeated HTTP lookups.
"""

from __future__ import annotations

import json
import logging
import urllib.request

from src.tools.registry import REGISTRY, ToolDefinition

_API_URL = "http://ip-api.com/json/?fields=status,message,city,regionName,country,countryCode,lat,lon"

# Module-level cache — populated on first call, reused for the session.
_cache: dict | None = None


def get_location() -> dict:
    """Resolve approximate location from the public IP address.

    Results are cached for the session.  On failure the dict contains
    an ``"error"`` key with a human-readable message.

    Returns:
        Dict with keys ``city``, ``region``, ``country``,
        ``country_code``, ``lat``, ``lon`` on success, or
        ``{"error": "<message>"}`` on failure.
    """
    global _cache
    if _cache is not None:
        return _cache

    try:
        with urllib.request.urlopen(_API_URL, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except Exception as exc:
        logging.warning("Location lookup failed: %s", exc)
        return {"error": str(exc)}

    if data.get("status") != "success":
        msg = data.get("message", "unknown error")
        logging.warning("Location API returned failure: %s", msg)
        return {"error": msg}

    _cache = {
        "city": data.get("city", ""),
        "region": data.get("regionName", ""),
        "country": data.get("country", ""),
        "country_code": data.get("countryCode", ""),
        "lat": data.get("lat"),
        "lon": data.get("lon"),
    }
    return _cache


def get_location_str() -> str:
    """Return a human-readable location string for use by other tools.

    Returns:
        A string such as ``"London, England, GB"``, or
        ``"Location unavailable"`` if the lookup failed.
    """
    loc = get_location()
    if "error" in loc:
        return "Location unavailable"
    parts = [p for p in (loc["city"], loc["region"], loc["country_code"]) if p]
    return ", ".join(parts) if parts else "Location unavailable"


def _handle_location_query(query: str) -> str:
    """Return a formatted location string for display in the chat.

    Args:
        query: The raw user query (not used — location is IP-derived).

    Returns:
        A human-readable location and coordinates string.
    """
    loc = get_location()
    if "error" in loc:
        return f"Could not determine location: {loc['error']}"
    location_str = get_location_str()
    lat = loc.get("lat")
    lon = loc.get("lon")
    has_coords = lat is not None and lon is not None
    coords = f" ({lat:.4f}, {lon:.4f})" if has_coords else ""
    return f"Your approximate location: {location_str}{coords}"


REGISTRY.register(
    ToolDefinition(
        name="location",
        router_tier="location",
        label="Tool: location",
        description=(
            "queries about the user's current location, where they are, "
            "or their city/country"
        ),
        examples=[
            "where am I",
            "what city am I in",
            "what is my location",
            "what country am I in",
        ],
        default_enabled=True,
        min_tier="trivial_llm",
        approach="A",
        callable=_handle_location_query,
        category="web",
    )
)
