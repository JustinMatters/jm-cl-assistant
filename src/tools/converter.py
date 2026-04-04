"""Unit conversion tool using pint.

Converts a numeric value between two units across common measurement
categories: length, mass, temperature, volume, speed, time, area,
energy, pressure, and data storage.
"""

import re as _re

import pint

from src.tools.registry import REGISTRY, ToolDefinition

_ureg = pint.UnitRegistry()
_ureg.formatter.default_format = "~P"  # abbreviated pretty format


def convert(value: float, from_unit: str, to_unit: str) -> str:
    """Convert a value from one unit to another.

    Args:
        value: The numeric quantity to convert.
        from_unit: The unit to convert from (e.g. ``"miles"``,
          ``"kg"``, ``"degF"``).
        to_unit: The unit to convert to (e.g. ``"km"``, ``"lb"``,
          ``"degC"``).

    Returns:
        A formatted string such as ``"5 mi = 8.047 km"``, or a
        human-readable error message if either unit is unknown or the
        units are incompatible.
    """
    try:
        quantity = _ureg.Quantity(value, from_unit)
        result = quantity.to(to_unit)
    except pint.errors.UndefinedUnitError as exc:
        return f"Error: unknown unit — {exc}"
    except pint.errors.DimensionalityError as exc:
        return f"Error: incompatible units — {exc}"
    except Exception as exc:
        return f"Error: {exc}"

    # Format the result value — drop trailing zeros after the decimal
    result_val = result.magnitude
    if isinstance(result_val, float):
        formatted = f"{result_val:.6g}"
    else:
        formatted = str(result_val)

    from_qty = _ureg.Quantity(value, from_unit)
    return f"{from_qty:~P} = {formatted} {result.units:~P}"


# Regex that extracts value, from-unit, and to-unit from a conversion query.
# e.g. "convert 5 miles to km" → ("5", "miles", "km")
_CONVERT_RE = _re.compile(
    r"(\d+(?:\.\d+)?)\s*([\w/]+(?:\s+\w+)??)\s+"
    r"(?:to|in|into)\s+([\w/]+(?:\s+\w+)?)",
    _re.IGNORECASE,
)


def _handle_convert_query(query: str) -> str | None:
    """Handle a raw conversion query by extracting arguments and converting.

    Args:
        query: The raw user query string,
          e.g. ``"convert 5 miles to km"``.

    Returns:
        A formatted conversion result string, or ``None`` if the query
        cannot be parsed or the conversion fails (signals fallback to LLM).
    """
    m = _CONVERT_RE.search(query)
    if not m:
        return None
    value = float(m.group(1))
    from_unit = m.group(2).strip()
    to_unit = m.group(3).strip()
    result = convert(value, from_unit, to_unit)
    return None if result.startswith("Error:") else result


REGISTRY.register(
    ToolDefinition(
        name="converter",
        router_tier="convert",
        label="Tool: converter",
        description=(
            "unit conversions: a number followed by a unit being "
            "converted to another unit"
        ),
        examples=[
            "convert 5 miles to km",
            "100 degF in celsius",
            "how many kg is 10 pounds",
            "60 mph to m/s",
        ],
        default_enabled=True,
        min_tier="trivial_ollama",
        approach="A",
        callable=_handle_convert_query,
        category="maths",
    )
)
