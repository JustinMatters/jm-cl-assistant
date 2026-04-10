"""Unit tests for Phase 23 — Streaming Responses.

Covers: chunk concatenation in stream_respond, TTS triggered only on
the final chunk, tool-use paths bypass streaming, and non-streaming
callers (respond) are unaffected.
"""

import numpy as np
import pytest

orchestrator_module = pytest.importorskip("src.orchestrator")
Orchestrator = orchestrator_module.Orchestrator

process_text_module = pytest.importorskip("src.process_text")
stream_process_text = process_text_module.stream_process_text

openrouter_module = pytest.importorskip("src.openrouter_client")
OpenRouterClient = openrouter_module.OpenRouterClient


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_orchestrator(mocker):
    """Return an Orchestrator with all heavy deps mocked."""
    mocker.patch("src.orchestrator.OllamaRouter")
    mocker.patch("src.orchestrator.OpenRouterClient")
    mocker.patch("src.orchestrator.MemoryStore")
    return Orchestrator(memory_enabled=False)


def _last_backend(orch):
    return lambda: orch.last_backend


# ── stream_respond: plain streaming path (no B-tool schemas) ──────────────────


class TestStreamRespondOllamaChunks:
    """stream_respond yields incremental chunks from Ollama."""

    def test_chunks_accumulate_correctly(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch.object(
            orch,
            "_ollama_stream",
            return_value=iter(["Hello", " world", "!"]),
        )
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])

        yields = list(orch.stream_respond("hi", []))

        # Last yield must be the fully accumulated text.
        final_text, final_history = yields[-1]
        assert final_text == "Hello world!"
        assert final_history is not None

    def test_intermediate_yields_have_none_history(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch.object(
            orch,
            "_ollama_stream",
            return_value=iter(["A", "B", "C"]),
        )
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])

        yields = list(orch.stream_respond("hi", []))

        # All intermediate yields must have None as history.
        for _text, hist in yields[:-1]:
            assert hist is None

    def test_final_yield_updates_history(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch.object(
            orch,
            "_ollama_stream",
            return_value=iter(["done"]),
        )
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])
        history = [{"role": "user", "content": "prev"}]

        _, final_history = list(orch.stream_respond("hi", history))[-1]

        assert final_history is not None
        roles = [m["role"] for m in final_history]
        assert "user" in roles
        assert "assistant" in roles


# ── stream_respond: Approach A tool path (single yield) ──────────────────────


class TestStreamRespondToolPath:
    def test_approach_a_yields_single_final_tuple(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "maths"
        mocker.patch(
            "src.orchestrator.REGISTRY.dispatch",
            return_value="42",
        )
        mocker.patch("src.orchestrator.REGISTRY.enabled_tools", return_value=[])

        yields = list(orch.stream_respond("2+2", []))

        assert len(yields) == 1
        text, hist = yields[0]
        assert text == "42"
        assert hist is not None

    def test_approach_a_history_includes_tool_response(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "maths"
        mocker.patch(
            "src.orchestrator.REGISTRY.dispatch",
            return_value="Result: 7",
        )
        mocker.patch("src.orchestrator.REGISTRY.enabled_tools", return_value=[])

        _, final_history = list(orch.stream_respond("q", []))[-1]

        assistant_msgs = [m for m in final_history if m["role"] == "assistant"]
        assert any("Result: 7" in m["content"] for m in assistant_msgs)


# ── stream_respond: Approach B tool schemas (non-streaming) ───────────────────


class TestStreamRespondBToolsBypass:
    def test_b_schemas_present_yields_single_tuple(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch(
            "src.orchestrator.REGISTRY.schemas",
            return_value=[{"type": "function"}],
        )
        mocker.patch.object(orch, "_ollama_respond", return_value="tool answer")
        mocker.patch.object(
            orch, "_make_b_executor", return_value=lambda n, a: ""
        )

        yields = list(orch.stream_respond("hi", []))

        assert len(yields) == 1
        _, hist = yields[0]
        assert hist is not None

    def test_b_schemas_calls_ollama_respond_not_stream(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch(
            "src.orchestrator.REGISTRY.schemas",
            return_value=[{"type": "function"}],
        )
        mock_respond = mocker.patch.object(
            orch, "_ollama_respond", return_value="answer"
        )
        mocker.patch.object(
            orch, "_make_b_executor", return_value=lambda n, a: ""
        )
        mock_stream = mocker.patch.object(
            orch, "_ollama_stream", return_value=iter([])
        )

        list(orch.stream_respond("hi", []))

        mock_respond.assert_called_once()
        mock_stream.assert_not_called()


# ── Non-streaming respond() unaffected ────────────────────────────────────────


class TestRespondUnaffected:
    def test_respond_still_returns_string_and_history(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])
        mocker.patch.object(
            orch, "_ollama_respond", return_value="static reply"
        )

        result, history = orch.respond("hi", [])

        assert isinstance(result, str)
        assert isinstance(history, list)

    def test_respond_not_a_generator(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])
        mocker.patch.object(orch, "_ollama_respond", return_value="reply")

        import types

        result = orch.respond("hi", [])
        assert not isinstance(result, types.GeneratorType)


# ── stream_process_text: TTS called only once ─────────────────────────────────


class TestStreamProcessTextTTS:
    def _make_mocks(self, mocker, chunks=("Hi", " there", "!")):
        orch = mocker.MagicMock()
        orch.last_backend = "Ollama: gemma4"
        orch.stream_respond.return_value = iter(
            [(c, None) for c in chunks[:-1]]
            + [(chunks[-1], [{"role": "user", "content": "hey"}])]
        )
        speaker = mocker.MagicMock()
        speaker.synthesize.return_value = (
            np.zeros(100, dtype=np.float32),
            24000,
        )
        return orch, speaker

    def test_tts_called_exactly_once(self, mocker):
        orch, spk = self._make_mocks(mocker)
        list(
            stream_process_text(
                "hey",
                [],
                "text and speech",
                True,
                "af_heart",
                orch,
                spk,
                _last_backend(orch),
            )
        )
        spk.synthesize.assert_called_once()

    def test_tts_called_with_full_response(self, mocker):
        orch, spk = self._make_mocks(mocker, chunks=("Hello", " world"))
        list(
            stream_process_text(
                "hey",
                [],
                "text and speech",
                True,
                "af_heart",
                orch,
                spk,
                _last_backend(orch),
            )
        )
        call_args = spk.synthesize.call_args[0][0]
        assert "world" in call_args

    def test_tts_not_called_in_text_mode(self, mocker):
        orch, spk = self._make_mocks(mocker)
        list(
            stream_process_text(
                "hey",
                [],
                "text",
                True,
                "af_heart",
                orch,
                spk,
                _last_backend(orch),
            )
        )
        spk.synthesize.assert_not_called()

    def test_intermediate_audio_is_none(self, mocker):
        orch, spk = self._make_mocks(mocker, chunks=("A", "B", "C"))
        results = list(
            stream_process_text(
                "hey",
                [],
                "text and speech",
                True,
                "af_heart",
                orch,
                spk,
                _last_backend(orch),
            )
        )
        for _, _, audio in results[:-1]:
            assert audio is None

    def test_final_yield_has_updated_history(self, mocker):
        orch, spk = self._make_mocks(mocker)
        results = list(
            stream_process_text(
                "hey",
                [],
                "text",
                True,
                "af_heart",
                orch,
                spk,
                _last_backend(orch),
            )
        )
        _, final_hist, _ = results[-1]
        assert final_hist is not None

    def test_intermediate_yields_have_none_history(self, mocker):
        orch, spk = self._make_mocks(mocker, chunks=("A", "B", "C"))
        results = list(
            stream_process_text(
                "hey",
                [],
                "text",
                True,
                "af_heart",
                orch,
                spk,
                _last_backend(orch),
            )
        )
        for _, hist, _ in results[:-1]:
            assert hist is None


# ── stream_process_text: OpenRouter streaming ─────────────────────────────────


class TestStreamAsk:
    def _mock_stream(self, mocker, chunks):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        chunk_mocks = []
        for text in chunks:
            c = mocker.MagicMock()
            c.choices[0].delta.content = text
            chunk_mocks.append(c)
        mock_create.return_value = iter(chunk_mocks)
        return mock_create

    def test_stream_ask_yields_chunks(self, mocker):
        self._mock_stream(mocker, ["Hello", " world"])
        client = OpenRouterClient()
        result = list(client.stream_ask("hi", "sonnet", []))
        assert result == ["Hello", " world"]

    def test_stream_ask_concatenates_to_full_text(self, mocker):
        self._mock_stream(mocker, ["The", " answer", " is", " 42"])
        client = OpenRouterClient()
        full = "".join(client.stream_ask("q", "sonnet", []))
        assert full == "The answer is 42"

    def test_stream_ask_skips_none_deltas(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        chunks = []
        for text in [None, "real", None, " content"]:
            c = mocker.MagicMock()
            c.choices[0].delta.content = text
            chunks.append(c)
        mock_create.return_value = iter(chunks)
        client = OpenRouterClient()
        result = list(client.stream_ask("hi", "sonnet", []))
        assert result == ["real", " content"]
