"""Unit tests for the image_gen tool.

All GPU and network calls are mocked.  No real model downloads or HTTP
requests are made.
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.tools.image_gen import (
    _generate_local,
    _image_gen_callable,
    _search_cc0,
)
from src.tools.image_utils import _IMAGE_PREFIX
from src.tools.registry import REGISTRY

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pil(width: int = 8, height: int = 8) -> Image.Image:
    return Image.new("RGB", (width, height), color="blue")


def _png_bytes(img: Image.Image | None = None) -> bytes:
    """Return raw PNG bytes for a small image."""
    buf = io.BytesIO()
    (img or _make_pil()).save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# _cuda_available
# ---------------------------------------------------------------------------


class TestCudaAvailable:
    def test_returns_true_when_cuda(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = True
        with patch.dict("sys.modules", {"torch": mock_torch}):
            import importlib

            import src.tools.image_gen as mod

            importlib.reload(mod)
            assert mod._cuda_available() is True

    def test_returns_false_when_no_cuda(self):
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        with patch.dict("sys.modules", {"torch": mock_torch}):
            import importlib

            import src.tools.image_gen as mod

            importlib.reload(mod)
            assert mod._cuda_available() is False

    def test_returns_false_on_import_error(self):
        with patch.dict("sys.modules", {"torch": None}):
            import importlib

            import src.tools.image_gen as mod

            importlib.reload(mod)
            assert mod._cuda_available() is False


# ---------------------------------------------------------------------------
# _generate_local
# ---------------------------------------------------------------------------


class TestGenerateLocal:
    def _mock_pipeline(self, img: Image.Image):
        """Return a mock pipeline that produces ``img``."""
        pipe = MagicMock()
        pipe.return_value.images = [img]
        return pipe

    def test_raises_when_no_cuda(self):
        with patch("src.tools.image_gen._cuda_available", return_value=False):
            with pytest.raises(RuntimeError, match="CUDA"):
                _generate_local("a cat")

    def test_returns_sentinel_bytes(self):
        img = _make_pil()
        mock_pipe_cls = MagicMock(return_value=self._mock_pipeline(img))

        import src.tools.image_gen as mod

        with (
            patch("src.tools.image_gen._cuda_available", return_value=True),
            patch("src.tools.image_gen._pipeline", None),
            patch("torch.float16", create=True),
            patch(
                "src.tools.image_gen.AutoPipelineForText2Image",
                mock_pipe_cls,
                create=True,
            ),
        ):
            # Patch module-level so pipeline init is skipped
            mod._pipeline = self._mock_pipeline(img)
            result = _generate_local("a cat")

        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)

    def test_caches_pipeline(self):
        """Second call must not re-instantiate the pipeline."""
        img = _make_pil()
        pipe = self._mock_pipeline(img)

        import src.tools.image_gen as mod

        original = mod._pipeline
        try:
            mod._pipeline = pipe
            with patch(
                "src.tools.image_gen._cuda_available", return_value=True
            ):
                _generate_local("prompt 1")
                _generate_local("prompt 2")
            assert pipe.call_count == 2  # called twice (inference), not init
        finally:
            mod._pipeline = original


# ---------------------------------------------------------------------------
# _search_cc0
# ---------------------------------------------------------------------------


class TestSearchCc0:
    def _fake_openverse(self, img_bytes: bytes):
        """Return a context-manager mock for urlopen."""
        import json as _json

        # First call: Openverse JSON response
        json_resp = MagicMock()
        json_resp.read.return_value = _json.dumps(
            {
                "results": [
                    {"url": "https://example.com/photo.png", "title": "cat"}
                ]
            }
        ).encode()
        json_resp.__enter__ = lambda s: s
        json_resp.__exit__ = lambda *a: None

        # Second call: raw image bytes
        img_resp = MagicMock()
        img_resp.read.return_value = img_bytes
        img_resp.__enter__ = lambda s: s
        img_resp.__exit__ = lambda *a: None

        return [json_resp, img_resp]

    def test_returns_sentinel_bytes(self):
        png = _png_bytes()
        responses = self._fake_openverse(png)

        with patch(
            "urllib.request.urlopen", side_effect=responses
        ) as mock_open:
            result = _search_cc0("cat")

        assert isinstance(result, bytes)
        assert result.startswith(_IMAGE_PREFIX)
        assert mock_open.call_count == 2

    def test_raises_when_no_results(self):
        import json as _json

        json_resp = MagicMock()
        json_resp.read.return_value = _json.dumps({"results": []}).encode()
        json_resp.__enter__ = lambda s: s
        json_resp.__exit__ = lambda *a: None

        with patch("urllib.request.urlopen", return_value=json_resp):
            with pytest.raises(ValueError, match="No CC0 images"):
                _search_cc0("xyzzy_no_results")

    def test_large_image_is_thumbnailed(self):
        big = Image.new("RGB", (2000, 2000), color="green")
        buf = io.BytesIO()
        big.save(buf, format="PNG")
        png = buf.getvalue()

        responses = self._fake_openverse(png)
        with patch("urllib.request.urlopen", side_effect=responses):
            result = _search_cc0("big landscape")

        # Decode and confirm dimensions were reduced
        from src.tools.image_utils import decode_image

        img = decode_image(result)
        assert max(img.size) <= 1024


# ---------------------------------------------------------------------------
# _image_gen_callable
# ---------------------------------------------------------------------------


class TestCallable:
    def test_invalid_json_returns_error(self):
        result = _image_gen_callable("not-json")
        assert "error" in result.lower()

    def test_missing_prompt_returns_error(self):
        result = _image_gen_callable(json.dumps({"mode": "auto"}))
        assert "prompt" in result.lower()

    def test_invalid_mode_returns_error(self):
        result = _image_gen_callable(
            json.dumps({"prompt": "cat", "mode": "dream"})
        )
        assert "error" in result.lower()

    def test_mode_local_no_cuda_returns_error(self):
        with patch("src.tools.image_gen._cuda_available", return_value=False):
            result = _image_gen_callable(
                json.dumps({"prompt": "a dog", "mode": "local"})
            )
        assert "error" in result.lower()

    def test_mode_search_returns_sentinel(self):
        sentinel = _IMAGE_PREFIX + b"fakedata"
        with patch("src.tools.image_gen._search_cc0", return_value=sentinel):
            result = _image_gen_callable(
                json.dumps({"prompt": "a cat", "mode": "search"})
            )
        assert result == sentinel

    def test_mode_search_failure_returns_error(self):
        with patch(
            "src.tools.image_gen._search_cc0",
            side_effect=ValueError("no results"),
        ):
            result = _image_gen_callable(
                json.dumps({"prompt": "xyzzy", "mode": "search"})
            )
        assert "error" in result.lower()

    def test_mode_local_returns_sentinel(self):
        sentinel = _IMAGE_PREFIX + b"fakedata"
        with (
            patch("src.tools.image_gen._cuda_available", return_value=True),
            patch("src.tools.image_gen._generate_local", return_value=sentinel),
        ):
            result = _image_gen_callable(
                json.dumps({"prompt": "a mountain", "mode": "local"})
            )
        assert result == sentinel

    def test_auto_uses_local_when_cuda(self):
        sentinel = _IMAGE_PREFIX + b"localdata"
        with (
            patch("src.tools.image_gen._cuda_available", return_value=True),
            patch(
                "src.tools.image_gen._generate_local", return_value=sentinel
            ) as mock_local,
            patch("src.tools.image_gen._search_cc0") as mock_search,
        ):
            result = _image_gen_callable(
                json.dumps({"prompt": "sunset", "mode": "auto"})
            )
        assert result == sentinel
        mock_local.assert_called_once()
        mock_search.assert_not_called()

    def test_auto_falls_back_to_search_when_no_cuda(self):
        sentinel = _IMAGE_PREFIX + b"searchdata"
        with (
            patch("src.tools.image_gen._cuda_available", return_value=False),
            patch("src.tools.image_gen._generate_local") as mock_local,
            patch(
                "src.tools.image_gen._search_cc0", return_value=sentinel
            ) as mock_search,
        ):
            result = _image_gen_callable(
                json.dumps({"prompt": "sunset", "mode": "auto"})
            )
        assert result == sentinel
        mock_local.assert_not_called()
        mock_search.assert_called_once()

    def test_auto_falls_back_to_search_when_local_fails(self):
        sentinel = _IMAGE_PREFIX + b"searchdata"
        with (
            patch("src.tools.image_gen._cuda_available", return_value=True),
            patch(
                "src.tools.image_gen._generate_local",
                side_effect=RuntimeError("OOM"),
            ),
            patch(
                "src.tools.image_gen._search_cc0", return_value=sentinel
            ) as mock_search,
        ):
            result = _image_gen_callable(
                json.dumps({"prompt": "sunset", "mode": "auto"})
            )
        assert result == sentinel
        mock_search.assert_called_once()

    def test_auto_both_fail_returns_error(self):
        with (
            patch("src.tools.image_gen._cuda_available", return_value=False),
            patch(
                "src.tools.image_gen._search_cc0",
                side_effect=ValueError("no results"),
            ),
        ):
            result = _image_gen_callable(
                json.dumps({"prompt": "xyzzy", "mode": "auto"})
            )
        assert "error" in result.lower() or "could not" in result.lower()

    def test_default_mode_is_auto(self):
        """Omitting mode should behave like 'auto'."""
        sentinel = _IMAGE_PREFIX + b"autodata"
        with (
            patch("src.tools.image_gen._cuda_available", return_value=False),
            patch("src.tools.image_gen._search_cc0", return_value=sentinel),
        ):
            result = _image_gen_callable(json.dumps({"prompt": "river"}))
        assert result == sentinel


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistration:
    def test_registered(self):
        assert any(t.name == "image_gen" for t in REGISTRY.all())

    def test_approach_b(self):
        tool = next(t for t in REGISTRY.all() if t.name == "image_gen")
        assert tool.approach == "B"

    def test_default_disabled(self):
        tool = next(t for t in REGISTRY.all() if t.name == "image_gen")
        assert tool.default_enabled is False

    def test_category_visual(self):
        tool = next(t for t in REGISTRY.all() if t.name == "image_gen")
        assert tool.category == "visual"

    def test_schema_required_fields(self):
        tool = next(t for t in REGISTRY.all() if t.name == "image_gen")
        assert "prompt" in tool.parameters_schema["required"]
