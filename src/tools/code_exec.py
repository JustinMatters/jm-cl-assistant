"""Code execution sandbox tool using asteval.

Executes Python expressions and statements in a restricted environment
that blocks imports, file I/O, and dangerous builtins.  Requires
explicit user approval (via UI modal) before any code runs.

Registered as Approach B (LLM function-calling), default-disabled, and
flagged ``requires_confirmation=True`` so the orchestrator pauses for
user approval instead of executing immediately.
"""

from __future__ import annotations

import json
from io import StringIO

from asteval import Interpreter

from src.tools.registry import REGISTRY, ToolDefinition

_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "code": {
            "type": "string",
            "description": (
                "Python code to execute in the sandbox. "
                "Imports and file I/O are not available."
            ),
        }
    },
    "required": ["code"],
    "additionalProperties": False,
}


def _run_code_callable(args_json: str) -> str:
    """Execute Python code via asteval and return output and result.

    Runs the supplied code in an asteval restricted interpreter.
    Stdout is captured via a ``StringIO`` writer.  Any error messages
    from the interpreter are returned instead of raising.

    Args:
        args_json: JSON string with a ``"code"`` key containing the
          Python source to evaluate.

    Returns:
        A string combining captured stdout and the final expression
        value, or an error description if execution failed.
    """
    try:
        args = json.loads(args_json)
    except json.JSONDecodeError as exc:
        return f"Error: invalid arguments — {exc}"

    code = args.get("code", "").strip()
    if not code:
        return "Error: no code provided."

    out = StringIO()
    aeval = Interpreter(writer=out, err_writer=out)
    result = aeval(code)
    output = out.getvalue()

    if aeval.error:
        error_msgs = "\n".join(str(e.get_error()[1]) for e in aeval.error)
        return f"Error:\n{error_msgs}"

    parts: list[str] = []
    if output:
        parts.append(output.rstrip())
    if result is not None and not output:
        # Only show repr if there was no printed output, to avoid
        # duplicating e.g. print() results that also return None.
        parts.append(repr(result))
    elif result is not None:
        parts.append(repr(result))
    return "\n".join(parts) if parts else "(no output)"


REGISTRY.register(
    ToolDefinition(
        name="code_exec",
        router_tier="code_exec",
        label="Tool: code execution (sandbox)",
        description=(
            "execute Python code snippets in a restricted sandbox; "
            "user must approve each execution before it runs"
        ),
        examples=[
            "calculate factorial of 15",
            "run this code: print(sum(range(100)))",
            "execute: [x**2 for x in range(10)]",
        ],
        default_enabled=False,
        min_tier="complex_sonnet",
        approach="B",
        callable=_run_code_callable,
        category="code",
        requires_confirmation=True,
        parameters_schema=_PARAMETERS_SCHEMA,
    )
)
