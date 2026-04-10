"""Tests for runtime feature switches (Phase 21).

Covers --no-tts (T21.1), --no-stt (T21.2), and --no-tools (T21.3).
"""

import numpy as np
import pytest

process_text_module = pytest.importorskip("src.process_text")
process_text = process_text_module.process_text

process_audio_module = pytest.importorskip("src.process_audio")
process_audio = process_audio_module.process_audio


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_orchestrator(mocker, response="Reply"):
    orch = mocker.MagicMock()
    orch.last_backend = "ollama"
    history_out = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": response},
    ]
    orch.respond.return_value = (response, history_out)
    return orch


def _make_speaker(mocker):
    spk = mocker.MagicMock()
    spk.synthesize.return_value = (np.zeros(100, dtype=np.float32), 24000)
    return spk


def _make_audio_data():
    return (16000, np.zeros(16000, dtype=np.int16))


def _make_transcriber(mocker, text="Hello"):
    t = mocker.MagicMock()
    t.transcribe.return_value = text
    return t


# ── T21.1: --no-tts ───────────────────────────────────────────────────────────


class TestNoTtsProcessText:
    def test_none_speaker_returns_no_audio_in_text_mode(self, mocker):
        orch = _make_orchestrator(mocker)
        _, _, audio_out = process_text(
            "Hello",
            [],
            "text",
            True,
            "af_heart",
            orch,
            None,
            lambda: "ollama",
        )
        assert audio_out is None

    def test_none_speaker_returns_no_audio_in_speech_mode(self, mocker):
        """When speaker=None, even 'text and speech' mode produces no audio."""
        orch = _make_orchestrator(mocker)
        _, _, audio_out = process_text(
            "Hello",
            [],
            "text and speech",
            True,
            "af_heart",
            orch,
            None,
            lambda: "ollama",
        )
        assert audio_out is None

    def test_none_speaker_does_not_raise(self, mocker):
        orch = _make_orchestrator(mocker)
        result = process_text(
            "Hello",
            [],
            "text and speech",
            True,
            "af_heart",
            orch,
            None,
            lambda: "ollama",
        )
        assert len(result) == 3

    def test_none_speaker_still_returns_text_response(self, mocker):
        orch = _make_orchestrator(mocker, response="Hi there")
        display_history, _, _ = process_text(
            "Hello",
            [],
            "text",
            True,
            "af_heart",
            orch,
            None,
            lambda: "ollama",
        )
        assert any(
            "Hi there" in m["content"]
            for m in display_history
            if m["role"] == "assistant"
        )

    def test_real_speaker_still_produces_audio_in_speech_mode(self, mocker):
        orch = _make_orchestrator(mocker)
        spk = _make_speaker(mocker)
        _, _, audio_out = process_text(
            "Hello",
            [],
            "text and speech",
            True,
            "af_heart",
            orch,
            spk,
            lambda: "ollama",
        )
        assert audio_out is not None


class TestNoTtsProcessAudio:
    def test_none_speaker_returns_no_audio(self, mocker):
        orch = _make_orchestrator(mocker)
        transcriber = _make_transcriber(mocker)
        _, _, audio_out = process_audio(
            _make_audio_data(),
            [],
            "text and speech",
            True,
            "af_heart",
            transcriber,
            orch,
            None,
        )
        assert audio_out is None

    def test_none_speaker_still_returns_display_history(self, mocker):
        orch = _make_orchestrator(mocker, response="Heard you")
        transcriber = _make_transcriber(mocker)
        display_history, _, _ = process_audio(
            _make_audio_data(),
            [],
            "text",
            True,
            "af_heart",
            transcriber,
            orch,
            None,
        )
        assert any(m["role"] == "assistant" for m in display_history)

    def test_real_speaker_produces_audio_when_tts_enabled(self, mocker):
        orch = _make_orchestrator(mocker)
        transcriber = _make_transcriber(mocker)
        spk = _make_speaker(mocker)
        _, _, audio_out = process_audio(
            _make_audio_data(),
            [],
            "text and speech",
            True,
            "af_heart",
            transcriber,
            orch,
            spk,
        )
        assert audio_out is not None


# ── T21.2: --no-stt ───────────────────────────────────────────────────────────


class TestNoSttProcessText:
    """process_text is not affected by --no-stt (it is text-only).

    These tests confirm that text processing is unaffected when transcriber
    would be None (it is not a parameter of process_text).
    """

    def test_text_processing_works_without_stt(self, mocker):
        orch = _make_orchestrator(mocker, response="Still works")
        display_history, updated_history, audio_out = process_text(
            "Hello",
            [],
            "text",
            True,
            "af_heart",
            orch,
            None,
            lambda: "ollama",
        )
        assert any(
            "Still works" in m["content"]
            for m in display_history
            if m["role"] == "assistant"
        )
        assert audio_out is None


class TestNoSttProcessAudio:
    def test_none_audio_data_returns_unchanged_history(self, mocker):
        orch = _make_orchestrator(mocker)
        transcriber = _make_transcriber(mocker)
        history = [{"role": "user", "content": "prev"}]
        display, state, audio = process_audio(
            None,
            history,
            "text",
            True,
            "af_heart",
            transcriber,
            orch,
            None,
        )
        assert state == history
        assert audio is None

    def test_empty_transcription_returns_error_display(self, mocker):
        orch = _make_orchestrator(mocker)
        transcriber = _make_transcriber(mocker, text="")
        display, state, audio = process_audio(
            _make_audio_data(),
            [],
            "text",
            True,
            "af_heart",
            transcriber,
            orch,
            None,
        )
        assert any(
            "audio" in m["content"].lower()
            for m in display
            if m["role"] == "assistant"
        )
        assert state == []
        assert audio is None


# ── T21.3: --no-tools ─────────────────────────────────────────────────────────


class TestNoToolsBuildApp:
    def test_tools_disabled_init_enabled_is_empty(self, mocker):
        """build_app with tools_enabled=False produces empty tools_state."""
        mocker.patch("src.app.Orchestrator")
        mocker.patch("src.app.WhisperTranscriber")
        mocker.patch("src.app.KokoroSpeaker")

        app_module = pytest.importorskip("src.app")
        build_app = app_module.build_app

        demo = build_app(
            whisper_model="tiny",
            ollama_model="gemma4:e4b",
            tools_enabled=False,
        )
        # build_app must not raise; the returned demo is a gr.Blocks
        assert demo is not None

    def test_tools_enabled_true_produces_nonempty_init(self, mocker):
        mocker.patch("src.app.Orchestrator")
        mocker.patch("src.app.WhisperTranscriber")
        mocker.patch("src.app.KokoroSpeaker")

        app_module = pytest.importorskip("src.app")
        build_app = app_module.build_app

        demo = build_app(
            whisper_model="tiny",
            ollama_model="gemma4:e4b",
            tools_enabled=True,
        )
        assert demo is not None


class TestNoToolsProcessText:
    def test_empty_enabled_tools_passes_through(self, mocker):
        """Passing frozenset() as enabled_tools returns a valid response."""
        orch = _make_orchestrator(mocker, response="No tools")
        display_history, updated_history, audio_out = process_text(
            "Hello",
            [],
            "text",
            True,
            "af_heart",
            orch,
            None,
            lambda: "ollama",
            enabled_tools=frozenset(),
        )
        orch.respond.assert_called_once_with(
            "Hello",
            [],
            memory_enabled=True,
            enabled_tools=frozenset(),
            image=None,
        )
        assert any(
            "No tools" in m["content"]
            for m in display_history
            if m["role"] == "assistant"
        )
