"""Unit tests for src/process_audio.py.

Covers _audio_err helper and all branches of process_audio:
guard conditions, dtype normalisation, transcription errors,
happy-path text and text+speech modes, and <think> tag filtering.
"""

import numpy as np
import pytest

process_audio_module = pytest.importorskip("src.process_audio")
process_audio = process_audio_module.process_audio
_audio_err = process_audio_module._audio_err


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_mocks(mocker, transcription="Hello world", response="Reply"):
    """Return (transcriber, orchestrator, speaker) mocks."""
    transcriber = mocker.MagicMock()
    transcriber.transcribe.return_value = transcription

    orchestrator = mocker.MagicMock()
    orchestrator.last_backend = "ollama"
    history_out = [
        {"role": "user", "content": "Hello world"},
        {"role": "assistant", "content": "Reply"},
    ]
    orchestrator.respond.return_value = (response, history_out)

    speaker = mocker.MagicMock()
    speaker.synthesize.return_value = (
        np.zeros(100, dtype=np.float32),
        24000,
    )
    return transcriber, orchestrator, speaker


def _int16_audio(length=1000):
    return np.zeros(length, dtype=np.int16)


def _float32_audio(length=1000):
    return np.zeros(length, dtype=np.float32)


# ── _audio_err ────────────────────────────────────────────────────────────────


class TestAudioErr:
    def test_returns_list(self):
        result = _audio_err([], "oops")
        assert isinstance(result, list)

    def test_appends_one_entry(self):
        result = _audio_err([], "oops")
        assert len(result) == 1

    def test_entry_is_assistant_role(self):
        result = _audio_err([], "oops")
        assert result[-1]["role"] == "assistant"

    def test_entry_contains_message(self):
        result = _audio_err([], "bad sample rate")
        assert "bad sample rate" in result[-1]["content"]

    def test_does_not_mutate_original_history(self):
        history = [{"role": "user", "content": "hi"}]
        original = list(history)
        _audio_err(history, "oops")
        assert history == original

    def test_preserves_existing_entries(self):
        history = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "there"},
        ]
        result = _audio_err(history, "oops")
        assert result[0] == history[0]
        assert result[1] == history[1]
        assert len(result) == 3


# ── Guard conditions ──────────────────────────────────────────────────────────


class TestProcessAudioGuards:
    def test_none_audio_data_returns_history_unchanged(self, mocker):
        t, o, s = _make_mocks(mocker)
        history = [{"role": "user", "content": "hi"}]
        display, state, audio = process_audio(
            None, history, "text", True, "af_heart", t, o, s
        )
        assert display is history
        assert state is history
        assert audio is None

    def test_none_audio_array_returns_history_unchanged(self, mocker):
        t, o, s = _make_mocks(mocker)
        history = []
        display, state, audio = process_audio(
            (16000, None), history, "text", True, "af_heart", t, o, s
        )
        assert display is history
        assert state is history
        assert audio is None

    def test_none_sample_rate_returns_history_unchanged(self, mocker):
        t, o, s = _make_mocks(mocker)
        history = []
        display, state, audio = process_audio(
            (None, _int16_audio()), history, "text", True, "af_heart", t, o, s
        )
        assert display is history
        assert state is history
        assert audio is None

    def test_empty_audio_array_returns_history_unchanged(self, mocker):
        t, o, s = _make_mocks(mocker)
        history = []
        display, state, audio = process_audio(
            (16000, np.array([], dtype=np.int16)),
            history,
            "text",
            True,
            "af_heart",
            t,
            o,
            s,
        )
        assert display is history
        assert state is history
        assert audio is None

    def test_zero_sample_rate_returns_error_bubble(self, mocker):
        t, o, s = _make_mocks(mocker)
        history = []
        display, state, audio = process_audio(
            (0, _int16_audio()), history, "text", True, "af_heart", t, o, s
        )
        assert any(
            "invalid sample rate" in m.get("content", "") for m in display
        )
        assert state is history
        assert audio is None

    def test_negative_sample_rate_returns_error_bubble(self, mocker):
        t, o, s = _make_mocks(mocker)
        history = []
        display, state, audio = process_audio(
            (-1, _int16_audio()), history, "text", True, "af_heart", t, o, s
        )
        assert any(
            "invalid sample rate" in m.get("content", "") for m in display
        )

    def test_non_numeric_sample_rate_returns_error_bubble(self, mocker):
        t, o, s = _make_mocks(mocker)
        history = []
        display, state, audio = process_audio(
            ("bad", _int16_audio()),
            history,
            "text",
            True,
            "af_heart",
            t,
            o,
            s,
        )
        assert any(
            "invalid sample rate" in m.get("content", "") for m in display
        )


# ── Dtype normalisation ───────────────────────────────────────────────────────


class TestProcessAudioNormalisation:
    """Verify transcriber receives a float32 array for each input dtype."""

    def _run(self, mocker, audio_array, sr=16000):
        t, o, s = _make_mocks(mocker)
        process_audio((sr, audio_array), [], "text", True, "af_heart", t, o, s)
        called_array = t.transcribe.call_args.args[0]
        return called_array

    def test_int16_normalised_to_float32(self, mocker):
        audio = (np.ones(100, dtype=np.int16) * 32767).astype(np.int16)
        result = self._run(mocker, audio)
        assert result.dtype == np.float32
        assert abs(result[0] - (32767 / 32768.0)) < 1e-4

    def test_float32_passthrough_unchanged(self, mocker):
        audio = np.full(100, 0.5, dtype=np.float32)
        result = self._run(mocker, audio)
        assert result.dtype == np.float32
        assert abs(result[0] - 0.5) < 1e-6

    def test_float64_cast_to_float32(self, mocker):
        audio = np.full(100, 0.5, dtype=np.float64)
        result = self._run(mocker, audio)
        assert result.dtype == np.float32

    def test_int32_normalised_to_float32(self, mocker):
        audio = np.array([2_147_483_647], dtype=np.int32)
        result = self._run(mocker, audio)
        assert result.dtype == np.float32
        assert abs(result[0] - 1.0) < 1e-6

    def test_transcriber_called_once(self, mocker):
        t, o, s = _make_mocks(mocker)
        process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        t.transcribe.assert_called_once()

    def test_transcriber_called_with_correct_sample_rate(self, mocker):
        t, o, s = _make_mocks(mocker)
        process_audio(
            (44100, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        _, sr_arg = t.transcribe.call_args.args
        assert sr_arg == 44100


# ── Transcription errors ──────────────────────────────────────────────────────


class TestProcessAudioTranscriptionErrors:
    def test_transcription_exception_returns_error_bubble(self, mocker):
        t, o, s = _make_mocks(mocker)
        t.transcribe.side_effect = RuntimeError("model failed")
        history = []
        display, state, audio = process_audio(
            (16000, _int16_audio()), history, "text", True, "af_heart", t, o, s
        )
        assert any(
            "transcription failed" in m.get("content", "") for m in display
        )
        assert state is history
        assert audio is None

    def test_empty_transcription_returns_error_bubble(self, mocker):
        t, o, s = _make_mocks(mocker, transcription="   ")
        history = []
        display, state, audio = process_audio(
            (16000, _int16_audio()), history, "text", True, "af_heart", t, o, s
        )
        assert any(
            "could not understand" in m.get("content", "") for m in display
        )
        assert state is history
        assert audio is None

    def test_orchestrator_not_called_on_empty_transcription(self, mocker):
        t, o, s = _make_mocks(mocker, transcription="")
        process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        o.respond.assert_not_called()


# ── Happy path — text mode ────────────────────────────────────────────────────


class TestProcessAudioTextMode:
    def test_returns_three_tuple(self, mocker):
        t, o, s = _make_mocks(mocker)
        result = process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        assert len(result) == 3

    def test_audio_out_is_none_in_text_mode(self, mocker):
        t, o, s = _make_mocks(mocker)
        _, _, audio = process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        assert audio is None

    def test_speaker_not_called_in_text_mode(self, mocker):
        t, o, s = _make_mocks(mocker)
        process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        s.synthesize.assert_not_called()

    def test_display_history_contains_backend_label(self, mocker):
        t, o, s = _make_mocks(mocker, response="Reply")
        o.last_backend = "claude-sonnet"
        display, _, _ = process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        last = display[-1]["content"]
        assert "**claude-sonnet:**" in last

    def test_display_history_contains_response(self, mocker):
        t, o, s = _make_mocks(mocker, response="My answer")
        display, _, _ = process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        last = display[-1]["content"]
        assert "My answer" in last

    def test_history_state_updated(self, mocker):
        t, o, s = _make_mocks(mocker)
        _, state, _ = process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        assert len(state) == 2  # user + assistant entries from mock

    def test_orchestrator_called_with_transcription(self, mocker):
        t, o, s = _make_mocks(mocker, transcription="What time is it?")
        process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        query_arg = o.respond.call_args.args[0]
        assert query_arg == "What time is it?"


# ── Happy path — text and speech mode ────────────────────────────────────────


class TestProcessAudioSpeechMode:
    def test_audio_out_not_none_in_speech_mode(self, mocker):
        t, o, s = _make_mocks(mocker)
        mocker.patch("src.process_audio.to_wav_bytes", return_value=b"WAVDATA")
        _, _, audio = process_audio(
            (16000, _int16_audio()),
            [],
            "text and speech",
            True,
            "af_heart",
            t,
            o,
            s,
        )
        assert audio is not None

    def test_speaker_called_in_speech_mode(self, mocker):
        t, o, s = _make_mocks(mocker)
        mocker.patch("src.process_audio.to_wav_bytes", return_value=b"WAV")
        process_audio(
            (16000, _int16_audio()),
            [],
            "text and speech",
            True,
            "af_heart",
            t,
            o,
            s,
        )
        s.synthesize.assert_called_once()

    def test_voice_passed_to_speaker(self, mocker):
        t, o, s = _make_mocks(mocker)
        mocker.patch("src.process_audio.to_wav_bytes", return_value=b"WAV")
        process_audio(
            (16000, _int16_audio()),
            [],
            "text and speech",
            True,
            "bm_george",
            t,
            o,
            s,
        )
        _, kwargs = s.synthesize.call_args
        assert kwargs["voice"] == "bm_george"

    def test_to_wav_bytes_result_returned(self, mocker):
        t, o, s = _make_mocks(mocker)
        mocker.patch("src.process_audio.to_wav_bytes", return_value=b"FAKEWAVE")
        _, _, audio = process_audio(
            (16000, _int16_audio()),
            [],
            "text and speech",
            True,
            "af_heart",
            t,
            o,
            s,
        )
        assert audio == b"FAKEWAVE"


# ── show=False strips think tags ──────────────────────────────────────────────


class TestProcessAudioShowThink:
    def test_show_true_keeps_think_tags(self, mocker):
        t, o, s = _make_mocks(mocker, response="<think>reasoning</think>Answer")
        o.respond.return_value = (
            "<think>reasoning</think>Answer",
            [
                {"role": "user", "content": "q"},
                {
                    "role": "assistant",
                    "content": "<think>reasoning</think>Answer",
                },
            ],
        )
        display, _, _ = process_audio(
            (16000, _int16_audio()), [], "text", True, "af_heart", t, o, s
        )
        assert "<think>" in display[-1]["content"]

    def test_show_false_strips_think_tags(self, mocker):
        t, o, s = _make_mocks(mocker, response="<think>reasoning</think>Answer")
        o.respond.return_value = (
            "<think>reasoning</think>Answer",
            [
                {"role": "user", "content": "q"},
                {
                    "role": "assistant",
                    "content": "<think>reasoning</think>Answer",
                },
            ],
        )
        display, _, _ = process_audio(
            (16000, _int16_audio()), [], "text", False, "af_heart", t, o, s
        )
        assert "<think>" not in display[-1]["content"]
        assert "Answer" in display[-1]["content"]

    def test_show_false_strips_think_in_speech_mode(self, mocker):
        t, o, s = _make_mocks(mocker, response="<think>hidden</think>Spoken")
        o.respond.return_value = (
            "<think>hidden</think>Spoken",
            [
                {"role": "user", "content": "q"},
                {
                    "role": "assistant",
                    "content": "<think>hidden</think>Spoken",
                },
            ],
        )
        mocker.patch("src.process_audio.to_wav_bytes", return_value=b"WAV")
        process_audio(
            (16000, _int16_audio()),
            [],
            "text and speech",
            False,
            "af_heart",
            t,
            o,
            s,
        )
        spoken_text = s.synthesize.call_args.args[0]
        assert "<think>" not in spoken_text
        assert "Spoken" in spoken_text
