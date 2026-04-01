"""Unit tests for src/process_text.py (T11.5 — Gradio handler crash protection).

Mirrors the structure of test_process_audio.py.
"""

import numpy as np
import pytest

process_text_module = pytest.importorskip("src.process_text")
process_text = process_text_module.process_text


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_mocks(mocker, response="Reply"):
    """Return (orchestrator, speaker) mocks with sensible defaults."""
    orchestrator = mocker.MagicMock()
    orchestrator.last_backend = "ollama"
    history_out = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": response},
    ]
    orchestrator.respond.return_value = (response, history_out)

    speaker = mocker.MagicMock()
    speaker.synthesize.return_value = (np.zeros(100, dtype=np.float32), 24000)

    return orchestrator, speaker


def _last_backend(orchestrator):
    return lambda: orchestrator.last_backend


def _call(
    mocker,
    query="Hello",
    history=None,
    out_mode="text",
    show=True,
    voice="af_heart",
    response="Reply",
):
    """Build mocks and call process_text with the given parameters."""
    orch, spk = _make_mocks(mocker, response=response)
    result = process_text(
        query,
        history if history is not None else [],
        out_mode,
        show,
        voice,
        orch,
        spk,
        _last_backend(orch),
    )
    return result, orch, spk


# ── Happy path ────────────────────────────────────────────────────────────────


class TestProcessTextHappyPath:
    def test_returns_three_tuple(self, mocker):
        result, _, _ = _call(mocker)
        assert isinstance(result, tuple) and len(result) == 3

    def test_display_history_has_backend_label(self, mocker):
        (display_history, _, _), _, _ = _call(mocker)
        last = display_history[-1]
        assert last["role"] == "assistant"
        assert "**ollama:**" in last["content"]

    def test_history_state_updated(self, mocker):
        (_, history_state, _), _, _ = _call(mocker)
        assert len(history_state) == 2

    def test_audio_none_in_text_mode(self, mocker):
        (_, _, audio_out), _, _ = _call(mocker, out_mode="text")
        assert audio_out is None

    def test_audio_returned_in_speech_mode(self, mocker):
        (_, _, audio_out), _, _ = _call(mocker, out_mode="text and speech")
        assert audio_out is not None

    def test_think_tags_stripped_when_show_false(self, mocker):
        (display_history, _, _), _, _ = _call(
            mocker, response="<think>reasoning</think>Answer", show=False
        )
        assert "<think>" not in display_history[-1]["content"]
        assert "Answer" in display_history[-1]["content"]

    def test_think_tags_kept_when_show_true(self, mocker):
        (display_history, _, _), _, _ = _call(
            mocker, response="<think>reasoning</think>Answer", show=True
        )
        assert "<think>" in display_history[-1]["content"]


# ── Crash protection ──────────────────────────────────────────────────────────


class TestProcessTextCrashProtection:
    def test_orchestrator_exception_returns_error_bubble(self, mocker):
        orch, spk = _make_mocks(mocker)
        orch.respond.side_effect = RuntimeError("downstream boom")
        display_history, history_state, audio_out = process_text(
            "Hello",
            [],
            "text",
            True,
            "af_heart",
            orch,
            spk,
            _last_backend(orch),
        )
        assert audio_out is None
        assert history_state == []
        last = display_history[-1]
        assert last["role"] == "assistant"
        assert "(Error:" in last["content"]

    def test_tts_exception_returns_error_bubble(self, mocker):
        orch, spk = _make_mocks(mocker)
        spk.synthesize.side_effect = RuntimeError("TTS crashed")
        display_history, history_state, audio_out = process_text(
            "Hello",
            [],
            "text and speech",
            True,
            "af_heart",
            orch,
            spk,
            _last_backend(orch),
        )
        assert audio_out is None
        assert history_state == []
        assert any(
            "(Error:" in m["content"]
            for m in display_history
            if m["role"] == "assistant"
        )

    def test_history_unchanged_on_error(self, mocker):
        existing = [{"role": "user", "content": "previous"}]
        orch, spk = _make_mocks(mocker)
        orch.respond.side_effect = ValueError("broken")
        _, history_state, _ = process_text(
            "Hello",
            existing,
            "text",
            True,
            "af_heart",
            orch,
            spk,
            _last_backend(orch),
        )
        assert history_state == existing

    def test_user_query_appears_in_error_display(self, mocker):
        orch, spk = _make_mocks(mocker)
        orch.respond.side_effect = RuntimeError("oops")
        display_history, _, _ = process_text(
            "my query",
            [],
            "text",
            True,
            "af_heart",
            orch,
            spk,
            _last_backend(orch),
        )
        assert any(
            m["role"] == "user" and "my query" in m["content"]
            for m in display_history
        )

    def test_connection_error_caught(self, mocker):
        orch, spk = _make_mocks(mocker)
        orch.respond.side_effect = ConnectionError("Ollama down")
        display_history, history_state, audio_out = process_text(
            "Hello",
            [],
            "text",
            True,
            "af_heart",
            orch,
            spk,
            _last_backend(orch),
        )
        assert audio_out is None
        assert history_state == []
        assert "(Error:" in display_history[-1]["content"]
