"""Safe arithmetic calculator tool using asteval.

Evaluates mathematical expressions without exposing ``eval`` to arbitrary
code. Supports basic arithmetic, exponentiation, modulo, parentheses, and
common maths functions via the asteval ``Interpreter``.
"""

import re as _re

from asteval import Interpreter

from src.tools.registry import REGISTRY, ToolDefinition

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


# Regex that strips natural-language preamble before passing to asteval.
# e.g. "what is 2+2?" → "2+2", "calculate sqrt(9)" → "sqrt(9)"
_MATHS_PREAMBLE = _re.compile(
    r"^\s*(?:what(?:'s|\s+is)?\s+|"
    r"calculate\s+|compute\s+|evaluate\s+|"
    r"solve\s+|find\s+|work\s+out\s+)",
    _re.IGNORECASE,
)


def _handle_maths_query(query: str) -> str | None:
    """Handle a raw maths query by stripping preamble and evaluating.

    Args:
        query: The raw user query string, e.g. ``"what is sqrt(144)?"``.

    Returns:
        The calculated result as a string, or ``None`` if asteval
        returns an error (signals the orchestrator to fall back to LLM).
    """
    expression = _MATHS_PREAMBLE.sub("", query).rstrip("?").strip()
    result = calculate(expression)
    return None if result.startswith("Error:") else result


REGISTRY.register(
    ToolDefinition(
        name="calculator",
        router_tier="maths",
        label="Tool: calculator",
        description=(
            "arithmetic, algebra, and any query whose answer is a number: "
            "expressions to evaluate, percentages, powers, roots, trigonometry"
        ),
        examples=[
            "what is 2+2",
            "calculate sqrt(144)",
            "15% of 200",
            "2**10",
        ],
        default_enabled=True,
        min_tier="trivial_llm",
        approach="A",
        callable=_handle_maths_query,
        category="maths",
    )
)
