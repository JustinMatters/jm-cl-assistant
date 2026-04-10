"""Unit tests for the flowchart tool.

graphviz.Source.pipe and PIL are mocked; no system binary is invoked.
"""

import json
from unittest.mock import patch

import graphviz
import pytest

from src.tools.flowchart import _flowchart_callable, render_dot
from src.tools.image_utils import _IMAGE_PREFIX
from src.tools.registry import REGISTRY

_SIMPLE_DOT = "digraph G { A -> B -> C; }"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20  # fake PNG header + body


class TestRenderDot:
    def test_calls_pipe(self):
        with patch("src.tools.flowchart.graphviz.Source") as mock_src:
            mock_src.return_value.pipe.return_value = _PNG_MAGIC
            result = render_dot(_SIMPLE_DOT)
        mock_src.assert_called_once_with(_SIMPLE_DOT, format="png")
        mock_src.return_value.pipe.assert_called_once()
        assert result == _PNG_MAGIC

    def test_propagates_executable_not_found(self):
        with patch("src.tools.flowchart.graphviz.Source") as mock_src:
            mock_src.return_value.pipe.side_effect = (
                graphviz.ExecutableNotFound(["dot"])
            )
            with pytest.raises(graphviz.ExecutableNotFound):
                render_dot(_SIMPLE_DOT)


class TestFlowchartCallable:
    def _mock_render(self, png_bytes=_PNG_MAGIC):
        """Patch render_dot and PIL.Image.open for a successful render."""

        from PIL import Image

        img = Image.new("RGB", (4, 4), color="white")

        def fake_open(buf):
            return img

        ctx_render = patch(
            "src.tools.flowchart.render_dot", return_value=png_bytes
        )
        ctx_pil = patch("src.tools.flowchart.Image.open", side_effect=fake_open)
        return ctx_render, ctx_pil

    def test_returns_image_sentinel_on_success(self):
        ctx_render, ctx_pil = self._mock_render()
        with ctx_render, ctx_pil:
            result = _flowchart_callable(json.dumps({"dot": _SIMPLE_DOT}))
        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)

    def test_missing_binary_returns_install_message(self):
        with patch(
            "src.tools.flowchart.render_dot",
            side_effect=graphviz.ExecutableNotFound(["dot"]),
        ):
            result = _flowchart_callable(json.dumps({"dot": _SIMPLE_DOT}))
        assert isinstance(result, str)
        assert "winget" in result
        assert "brew" in result

    def test_render_error_returns_string(self):
        with patch(
            "src.tools.flowchart.render_dot",
            side_effect=Exception("syntax error in DOT"),
        ):
            result = _flowchart_callable(json.dumps({"dot": _SIMPLE_DOT}))
        assert isinstance(result, str)
        assert "error" in result.lower()

    def test_empty_dot_returns_error(self):
        result = _flowchart_callable(json.dumps({"dot": ""}))
        assert isinstance(result, str)
        assert "no DOT source" in result

    def test_missing_dot_key_returns_error(self):
        result = _flowchart_callable(json.dumps({}))
        assert isinstance(result, str)
        assert "no DOT source" in result

    def test_invalid_json_returns_error(self):
        result = _flowchart_callable("not-json")
        assert isinstance(result, str)
        assert "invalid" in result.lower()

    def test_whitespace_only_dot_returns_error(self):
        result = _flowchart_callable(json.dumps({"dot": "   "}))
        assert isinstance(result, str)


class TestRegistration:
    def test_registered(self):
        assert any(t.name == "flowchart" for t in REGISTRY.all())

    def test_approach_b(self):
        tool = next(t for t in REGISTRY.all() if t.name == "flowchart")
        assert tool.approach == "B"

    def test_default_enabled(self):
        tool = next(t for t in REGISTRY.all() if t.name == "flowchart")
        assert tool.default_enabled is True

    def test_schema_has_dot_param(self):
        tool = next(t for t in REGISTRY.all() if t.name == "flowchart")
        assert "dot" in tool.parameters_schema["properties"]
        assert "dot" in tool.parameters_schema["required"]
