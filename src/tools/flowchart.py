"""Flowchart generation tool using Graphviz DOT notation.

Approach B tool — the LLM generates valid Graphviz DOT source and this
tool renders it to a PNG image returned via the __IMAGE__: sentinel.

Requires the Graphviz system binary to be installed separately:
  Windows : winget install graphviz
  macOS   : brew install graphviz
  Linux   : apt install graphviz  (or equivalent)
"""

from __future__ import annotations

import json
import logging

import graphviz
from PIL import Image

from src.tools.image_utils import encode_image
from src.tools.registry import REGISTRY, ToolDefinition

_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "dot": {
            "type": "string",
            "description": (
                "Valid Graphviz DOT source for the flowchart. "
                "Output ONLY the raw DOT source — no markdown fences, "
                "no commentary, no explanation."
            ),
        }
    },
    "required": ["dot"],
    "additionalProperties": False,
}

_INSTALL_MSG = (
    "Graphviz system binary not found. "
    "Install it then restart the app:\n"
    "  Windows : winget install graphviz\n"
    "  macOS   : brew install graphviz\n"
    "  Linux   : sudo apt install graphviz"
)


def render_dot(dot: str) -> bytes:
    """Render a Graphviz DOT string to PNG bytes.

    Args:
        dot: Valid Graphviz DOT source text.

    Returns:
        PNG image as raw bytes.

    Raises:
        graphviz.ExecutableNotFound: If the Graphviz system binary is missing.
        graphviz.CalledProcessError: If DOT source contains syntax errors.
    """
    return graphviz.Source(dot, format="png").pipe()


def _flowchart_callable(args_json: str) -> bytes | str:
    """Approach B callable — parses JSON args and renders a flowchart.

    Args:
        args_json: JSON string with a ``dot`` key containing DOT source.

    Returns:
        Image sentinel bytes on success, or an error string.
    """
    try:
        args = json.loads(args_json)
        dot = args.get("dot", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return "Error: invalid arguments for flowchart tool."

    if not dot:
        return "Error: no DOT source provided."

    try:
        png_bytes = render_dot(dot)
    except graphviz.ExecutableNotFound:
        return _INSTALL_MSG
    except Exception as exc:
        logging.warning("Flowchart render failed: %s", exc)
        return f"Flowchart render error: {exc}"

    try:
        import io

        img = Image.open(io.BytesIO(png_bytes))
        return encode_image(img)
    except Exception as exc:
        logging.warning("Flowchart image encode failed: %s", exc)
        return f"Image encode error: {exc}"


REGISTRY.register(
    ToolDefinition(
        name="flowchart",
        router_tier="flowchart",
        label="Tool: Flowchart",
        description=(
            "generate a flowchart or diagram from a description; "
            "produces a PNG image using Graphviz DOT notation"
        ),
        examples=[
            "draw a flowchart of the login process",
            "create a diagram showing the steps to make tea",
            "make a flowchart for a binary search algorithm",
            "diagram the states of a traffic light",
        ],
        default_enabled=True,
        min_tier="advanced_llm",
        approach="B",
        callable=_flowchart_callable,
        category="visual",
        parameters_schema=_PARAMETERS_SCHEMA,
    )
)
