"""Unit tests for vision API support (T20.5).

Tests cover:
- orchestrator routing upgrade when image is attached
- Ollama image encoding in _ollama_respond
- OpenRouterClient image content block construction
- _model_supports_vision helper
"""

import base64
from unittest.mock import MagicMock, patch

from PIL import Image

from src.openrouter_client import OpenRouterClient
from src.orchestrator import Orchestrator, _model_supports_vision

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pil(
    width: int = 4, height: int = 4, color: str = "red"
) -> Image.Image:
    return Image.new("RGB", (width, height), color=color)


def _make_orchestrator(ollama_model: str = "gemma4:e4b") -> Orchestrator:
    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
        orc = Orchestrator(
            ollama_model=ollama_model,
            fast_model="qwen3:1.7b",
            memory_enabled=False,
        )
    return orc


# ---------------------------------------------------------------------------
# _model_supports_vision
# ---------------------------------------------------------------------------


class TestModelSupportsVision:
    def test_gemma4_supported(self):
        assert _model_supports_vision("gemma4:e4b") is True

    def test_gemma4_with_registry_prefix(self):
        assert _model_supports_vision("google/gemma4:12b") is True

    def test_llava_supported(self):
        assert _model_supports_vision("llava:13b") is True

    def test_moondream_supported(self):
        assert _model_supports_vision("moondream:latest") is True

    def test_deepseek_not_supported(self):
        assert _model_supports_vision("deepseek-r1:8b") is False

    def test_qwen3_not_supported(self):
        assert _model_supports_vision("qwen3:1.7b") is False

    def test_empty_string_not_supported(self):
        assert _model_supports_vision("") is False


# ---------------------------------------------------------------------------
# Routing escalation
# ---------------------------------------------------------------------------


class TestRoutingEscalation:
    """When an image is attached and the Ollama model lacks vision, the
    orchestrator must escalate to complex_sonnet."""

    def _mock_router(self, orc, tier: str):
        orc._router.classify = MagicMock(return_value=tier)

    def test_trivial_escalates_to_sonnet_for_non_vision_model(self, mocker):
        orc = _make_orchestrator(ollama_model="deepseek-r1:8b")
        orc._fast_model = "qwen3:1.7b"  # non-vision
        self._mock_router(orc, "trivial_ollama")
        mock_ask = mocker.patch.object(
            orc._claude, "ask", return_value="Claude response"
        )
        img = _make_pil()
        orc.respond("describe this", [], image=img)
        mock_ask.assert_called_once()
        args, kwargs = mock_ask.call_args
        assert args[1] == "sonnet"
        assert kwargs.get("image") is img or kwargs["image"] is img

    def test_simple_escalates_to_sonnet_for_non_vision_model(self, mocker):
        orc = _make_orchestrator(ollama_model="deepseek-r1:8b")
        self._mock_router(orc, "simple_ollama")
        mock_ask = mocker.patch.object(
            orc._claude, "ask", return_value="Claude response"
        )
        img = _make_pil()
        orc.respond("describe this", [], image=img)
        mock_ask.assert_called_once()

    def test_vision_model_stays_local(self, mocker):
        orc = _make_orchestrator(ollama_model="gemma4:e4b")
        self._mock_router(orc, "simple_ollama")
        mock_ollama = mocker.patch("src.orchestrator.ollama.chat")
        mock_ollama.return_value = {
            "message": {"content": "Ollama response", "tool_calls": None}
        }
        img = _make_pil()
        response, _ = orc.respond("describe this", [], image=img)
        mock_ollama.assert_called_once()
        assert "Ollama response" in response

    def test_no_image_does_not_escalate(self, mocker):
        orc = _make_orchestrator(ollama_model="deepseek-r1:8b")
        self._mock_router(orc, "trivial_ollama")
        mock_ollama = mocker.patch("src.orchestrator.ollama.chat")
        mock_ollama.return_value = {
            "message": {"content": "Ollama response", "tool_calls": None}
        }
        response, _ = orc.respond("hello", [], image=None)
        mock_ollama.assert_called_once()


# ---------------------------------------------------------------------------
# Ollama image encoding
# ---------------------------------------------------------------------------


class TestOllamaImageEncoding:
    def test_image_added_to_user_message(self, mocker):
        orc = _make_orchestrator(ollama_model="gemma4:e4b")
        captured_messages = []

        def fake_chat(**kwargs):
            captured_messages.extend(kwargs["messages"])
            return {"message": {"content": "ok", "tool_calls": None}}

        mocker.patch("src.orchestrator.ollama.chat", side_effect=fake_chat)
        img = _make_pil()
        orc._ollama_respond("hi", [], "gemma4:e4b", image=img)

        user_msg = next(m for m in captured_messages if m["role"] == "user")
        assert "images" in user_msg
        assert len(user_msg["images"]) == 1
        # Verify it's valid base64 PNG
        raw = base64.b64decode(user_msg["images"][0])
        assert raw[:4] == b"\x89PNG"

    def test_no_image_omits_images_key(self, mocker):
        orc = _make_orchestrator()
        captured_messages = []

        def fake_chat(**kwargs):
            captured_messages.extend(kwargs["messages"])
            return {"message": {"content": "ok", "tool_calls": None}}

        mocker.patch("src.orchestrator.ollama.chat", side_effect=fake_chat)
        orc._ollama_respond("hi", [], "gemma4:e4b", image=None)

        user_msg = next(m for m in captured_messages if m["role"] == "user")
        assert "images" not in user_msg


# ---------------------------------------------------------------------------
# OpenRouterClient image encoding
# ---------------------------------------------------------------------------


class TestOpenRouterImageEncoding:
    def _make_client(self):
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
            return OpenRouterClient()

    def _mock_completion(self, mocker, content: str = "response"):
        choice = MagicMock()
        choice.finish_reason = "stop"
        choice.message.content = content
        completion = MagicMock()
        completion.choices = [choice]
        return mocker.patch.object(
            OpenRouterClient,
            "_client",
            new_callable=lambda: property(
                lambda self: MagicMock(
                    chat=MagicMock(
                        completions=MagicMock(
                            create=MagicMock(return_value=completion)
                        )
                    )
                )
            ),
        )

    def test_image_produces_content_list(self, mocker):
        client = self._make_client()
        captured = []

        def fake_create(messages, **kwargs):
            captured.extend(messages)
            choice = MagicMock()
            choice.finish_reason = "stop"
            choice.message.content = "ok"
            result = MagicMock()
            result.choices = [choice]
            return result

        mocker.patch.object(
            client._client.chat.completions, "create", side_effect=fake_create
        )
        img = _make_pil()
        client.ask("describe this", "sonnet", [], image=img)

        user_msg = next(m for m in captured if m["role"] == "user")
        assert isinstance(user_msg["content"], list)
        types = [block["type"] for block in user_msg["content"]]
        assert "text" in types
        assert "image_url" in types

    def test_image_url_is_base64_png(self, mocker):
        client = self._make_client()
        captured = []

        def fake_create(messages, **kwargs):
            captured.extend(messages)
            choice = MagicMock()
            choice.finish_reason = "stop"
            choice.message.content = "ok"
            result = MagicMock()
            result.choices = [choice]
            return result

        mocker.patch.object(
            client._client.chat.completions, "create", side_effect=fake_create
        )
        img = _make_pil()
        client.ask("describe this", "sonnet", [], image=img)

        user_msg = next(m for m in captured if m["role"] == "user")
        img_block = next(
            b for b in user_msg["content"] if b["type"] == "image_url"
        )
        url = img_block["image_url"]["url"]
        assert url.startswith("data:image/png;base64,")
        b64_part = url[len("data:image/png;base64,") :]
        raw = base64.b64decode(b64_part)
        assert raw[:4] == b"\x89PNG"

    def test_no_image_sends_plain_string(self, mocker):
        client = self._make_client()
        captured = []

        def fake_create(messages, **kwargs):
            captured.extend(messages)
            choice = MagicMock()
            choice.finish_reason = "stop"
            choice.message.content = "ok"
            result = MagicMock()
            result.choices = [choice]
            return result

        mocker.patch.object(
            client._client.chat.completions, "create", side_effect=fake_create
        )
        client.ask("hello", "sonnet", [], image=None)

        user_msg = next(m for m in captured if m["role"] == "user")
        assert isinstance(user_msg["content"], str)
