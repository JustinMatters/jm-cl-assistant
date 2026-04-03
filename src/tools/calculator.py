"""Safe arithmetic calculator tool using asteval.

Evaluates mathematical expressions without exposing ``eval`` to arbitrary
code. Supports basic arithmetic, exponentiation, modulo, parentheses, and
common maths functions via the asteval ``Interpreter``.
"""

from asteval import Interpreter

_AEVAL = Interpreter(minimal=True, use_numpy=False)

# Explicitly add the maths functions we want to expose
_AEVAL.symtable.update(
    {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
    }
)

# Pull in standard maths functions from the math module
import math as _math  # noqa: E402

for _name in (
    "sqrt",
    "ceil",
    "floor",
    "log",
    "log2",
    "log10",
    "exp",
    "sin",
    "cos",
    "tan",
    "asin",
    "acos",
    "atan",
    "atan2",
    "degrees",
    "radians",
    "factorial",
    "gcd",
    "pi",
    "e",
    "tau",
    "inf",
):
    if hasattr(_math, _name):
        _AEVAL.symtable[_name] = getattr(_math, _name)


def calculate(expression: str) -> str:
    """Evaluate a mathematical expression and return the result as a string.

    Uses asteval's restricted interpreter — arbitrary Python statements,
    imports, and attribute access are not permitted.

    Args:
        expression: A mathematical expression string, e.g.
          ``"sqrt(2) * pi"`` or ``"(3 + 4) * 2"``

    Returns:
        The numeric result formatted as a string, or a human-readable error
        message if the expression is invalid or raises an exception.
    """
    _AEVAL.error.clear()
    result = _AEVAL.eval(expression.strip())

    if _AEVAL.error:
        msgs = "; ".join(str(e.get_error()) for e in _AEVAL.error)
        return f"Error: {msgs}"

    if result is None:
        return "Error: expression produced no result"

    # Format integers without a trailing decimal point
    if isinstance(result, float) and result.is_integer():
        return str(int(result))

    return str(result)
