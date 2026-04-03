"""Unit conversion tool using pint.

Converts a numeric value between two units across common measurement
categories: length, mass, temperature, volume, speed, time, area,
energy, pressure, and data storage.
"""

import pint

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
