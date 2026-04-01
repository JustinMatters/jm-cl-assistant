import numpy as np
import pytest

speech_input_module = pytest.importorskip("src.speech_input")
speech_output_module = pytest.importorskip("src.speech_output")
WhisperTranscriber = speech_input_module.WhisperTranscriber
KokoroSpeaker = speech_output_module.KokoroSpeaker
check_kokoro_files = speech_output_module.check_kokoro_files


class TestWhisperTranscriber:
    def test_transcribe_returns_string(self, mocker):
        mocker.patch("src.speech_input.whisper.load_model")
        mock_model = mocker.MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}
        mocker.patch(
            "src.speech_input.whisper.load_model",
            return_value=mock_model,
        )
        transcriber = WhisperTranscriber()
        audio = np.zeros(16000, dtype=np.float32)
        result = transcriber.transcribe(audio, 16000)
        assert isinstance(result, str)

    def test_transcribe_returns_expected_text(self, mocker):
        mock_model = mocker.MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}
        mocker.patch(
            "src.speech_input.whisper.load_model",
            return_value=mock_model,
        )
        transcriber = WhisperTranscriber()
        audio = np.zeros(16000, dtype=np.float32)
        result = transcriber.transcribe(audio, 16000)
        assert result == "Hello world"

    def test_default_model_is_medium(self, mocker):
        mock_load = mocker.patch("src.speech_input.whisper.load_model")
        mock_load.return_value = mocker.MagicMock()
        mock_load.return_value.transcribe.return_value = {"text": ""}
        transcriber = WhisperTranscriber()
        transcriber.transcribe(np.zeros(16000, dtype=np.float32), 16000)
        mock_load.assert_called_once_with("medium")

    def test_model_loaded_lazily_on_first_call(self, mocker):
        mock_load = mocker.patch("src.speech_input.whisper.load_model")
        mock_load.return_value = mocker.MagicMock()
        mock_load.return_value.transcribe.return_value = {"text": ""}
        transcriber = WhisperTranscriber()
        mock_load.assert_not_called()
        transcriber.transcribe(np.zeros(16000, dtype=np.float32), 16000)
        mock_load.assert_called_once()

    def test_model_not_reloaded_on_second_call(self, mocker):
        mock_load = mocker.patch("src.speech_input.whisper.load_model")
        mock_load.return_value = mocker.MagicMock()
        mock_load.return_value.transcribe.return_value = {"text": ""}
        transcriber = WhisperTranscriber()
        audio = np.zeros(16000, dtype=np.float32)
        transcriber.transcribe(audio, 16000)
        transcriber.transcribe(audio, 16000)
        mock_load.assert_called_once()

    def test_transcribe_called_with_audio_array(self, mocker):
        mock_model = mocker.MagicMock()
        mock_model.transcribe.return_value = {"text": "test"}
        mocker.patch(
            "src.speech_input.whisper.load_model",
            return_value=mock_model,
        )
        transcriber = WhisperTranscriber()
        audio = np.zeros(16000, dtype=np.float32)
        transcriber.transcribe(audio, 16000)
        mock_model.transcribe.assert_called_once()

    def test_transcribe_handles_silent_audio(self, mocker):
        mock_model = mocker.MagicMock()
        mock_model.transcribe.return_value = {"text": ""}
        mocker.patch(
            "src.speech_input.whisper.load_model",
            return_value=mock_model,
        )
        transcriber = WhisperTranscriber()
        silent_audio = np.zeros(16000, dtype=np.float32)
        result = transcriber.transcribe(silent_audio, 16000)
        assert isinstance(result, str)

    def test_high_no_speech_prob_returns_empty(self, mocker):
        mock_model = mocker.MagicMock()
        mock_model.transcribe.return_value = {
            "text": "maybe some hallucinated text",
            "segments": [{"no_speech_prob": 0.95}],
        }
        mocker.patch(
            "src.speech_input.whisper.load_model",
            return_value=mock_model,
        )
        transcriber = WhisperTranscriber()
        audio = np.zeros(16000, dtype=np.float32)
        result = transcriber.transcribe(audio, 16000)
        assert result == ""

    def test_low_no_speech_prob_returns_text(self, mocker):
        mock_model = mocker.MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello world",
            "segments": [{"no_speech_prob": 0.05}],
        }
        mocker.patch(
            "src.speech_input.whisper.load_model",
            return_value=mock_model,
        )
        transcriber = WhisperTranscriber()
        audio = np.zeros(16000, dtype=np.float32)
        result = transcriber.transcribe(audio, 16000)
        assert result == "Hello world"

    def test_no_segments_returns_text(self, mocker):
        mock_model = mocker.MagicMock()
        mock_model.transcribe.return_value = {"text": "Hello world"}
        mocker.patch(
            "src.speech_input.whisper.load_model",
            return_value=mock_model,
        )
        transcriber = WhisperTranscriber()
        audio = np.zeros(16000, dtype=np.float32)
        result = transcriber.transcribe(audio, 16000)
        assert result == "Hello world"


class TestKokoroSpeaker:
    def test_synthesize_returns_tuple(self, mocker):
        mocker.patch("src.speech_output.Kokoro")
        mock_kokoro = mocker.MagicMock()
        fake_audio = np.zeros(22050, dtype=np.float32)
        mock_kokoro.create.return_value = (fake_audio, 24000)
        mocker.patch("src.speech_output.Kokoro", return_value=mock_kokoro)
        speaker = KokoroSpeaker()
        result = speaker.synthesize("Hello world")
        assert isinstance(result, tuple)

    def test_synthesize_returns_ndarray_and_int(self, mocker):
        mock_kokoro = mocker.MagicMock()
        fake_audio = np.zeros(22050, dtype=np.float32)
        mock_kokoro.create.return_value = (fake_audio, 24000)
        mocker.patch("src.speech_output.Kokoro", return_value=mock_kokoro)
        speaker = KokoroSpeaker()
        audio, sample_rate = speaker.synthesize("Hello world")
        assert isinstance(audio, np.ndarray)
        assert isinstance(sample_rate, int)

    def test_synthesize_returns_nonzero_sample_rate(self, mocker):
        mock_kokoro = mocker.MagicMock()
        fake_audio = np.zeros(22050, dtype=np.float32)
        mock_kokoro.create.return_value = (fake_audio, 24000)
        mocker.patch("src.speech_output.Kokoro", return_value=mock_kokoro)
        speaker = KokoroSpeaker()
        _, sample_rate = speaker.synthesize("Hello")
        assert sample_rate > 0

    def test_model_loaded_lazily_on_first_call(self, mocker):
        mock_kokoro_cls = mocker.patch("src.speech_output.Kokoro")
        mock_kokoro_cls.return_value.create.return_value = (
            np.zeros(100, dtype=np.float32),
            24000,
        )
        speaker = KokoroSpeaker()
        mock_kokoro_cls.assert_not_called()
        speaker.synthesize("Hello")
        mock_kokoro_cls.assert_called_once()

    def test_model_not_reloaded_on_second_call(self, mocker):
        mock_kokoro_cls = mocker.patch("src.speech_output.Kokoro")
        mock_kokoro_cls.return_value.create.return_value = (
            np.zeros(100, dtype=np.float32),
            24000,
        )
        speaker = KokoroSpeaker()
        speaker.synthesize("Hello")
        speaker.synthesize("World")
        mock_kokoro_cls.assert_called_once()

    def test_default_paths_passed_to_kokoro(self, mocker):
        mock_kokoro_cls = mocker.patch("src.speech_output.Kokoro")
        mock_kokoro_cls.return_value.create.return_value = (
            np.zeros(100, dtype=np.float32),
            24000,
        )
        speaker = KokoroSpeaker()
        speaker.synthesize("Hello")
        mock_kokoro_cls.assert_called_once_with(
            "kokoro-v1.0.onnx", "voices-v1.0.bin"
        )

    def test_custom_paths_passed_to_kokoro(self, mocker):
        mock_kokoro_cls = mocker.patch("src.speech_output.Kokoro")
        mock_kokoro_cls.return_value.create.return_value = (
            np.zeros(100, dtype=np.float32),
            24000,
        )
        speaker = KokoroSpeaker(
            model_path="custom.onnx", voices_path="custom.bin"
        )
        speaker.synthesize("Hello")
        mock_kokoro_cls.assert_called_once_with("custom.onnx", "custom.bin")

    def test_create_called_with_voice_and_speed(self, mocker):
        mock_kokoro_cls = mocker.patch("src.speech_output.Kokoro")
        mock_instance = mock_kokoro_cls.return_value
        mock_instance.create.return_value = (
            np.zeros(100, dtype=np.float32),
            24000,
        )
        speaker = KokoroSpeaker(voice="am_adam", speed=1.2)
        speaker.synthesize("Hello")
        mock_instance.create.assert_called_once_with(
            "Hello", voice="am_adam", speed=1.2
        )

    def test_voice_override_passed_to_create(self, mocker):
        mock_kokoro_cls = mocker.patch("src.speech_output.Kokoro")
        mock_instance = mock_kokoro_cls.return_value
        mock_instance.create.return_value = (
            np.zeros(100, dtype=np.float32),
            24000,
        )
        speaker = KokoroSpeaker()
        speaker.synthesize("Hello", voice="am_michael")
        _, kwargs = mock_instance.create.call_args
        assert kwargs["voice"] == "am_michael"

    def test_default_voice_is_af_heart(self, mocker):
        mock_kokoro_cls = mocker.patch("src.speech_output.Kokoro")
        mock_instance = mock_kokoro_cls.return_value
        mock_instance.create.return_value = (
            np.zeros(100, dtype=np.float32),
            24000,
        )
        speaker = KokoroSpeaker()
        speaker.synthesize("Hello")
        _, kwargs = mock_instance.create.call_args
        assert kwargs["voice"] == "af_heart"

    def test_synthesize_raises_clearly_on_missing_model_files(self, mocker):
        mocker.patch(
            "src.speech_output.Kokoro",
            side_effect=FileNotFoundError("kokoro-v1.0.onnx not found"),
        )
        speaker = KokoroSpeaker()
        with pytest.raises(FileNotFoundError, match="Kokoro model files"):
            speaker.synthesize("Hello")

    def test_synthesize_raises_clearly_on_corrupt_model(self, mocker):
        mocker.patch(
            "src.speech_output.Kokoro",
            side_effect=RuntimeError("invalid ONNX model"),
        )
        speaker = KokoroSpeaker()
        with pytest.raises(RuntimeError, match="Kokoro model failed to load"):
            speaker.synthesize("Hello")


class TestCheckKokoroFiles:
    def test_returns_none_when_both_files_present(self, mocker):
        mocker.patch(
            "src.speech_output.Path.exists",
            return_value=True,
        )
        assert check_kokoro_files() is None

    def test_returns_warning_when_both_files_missing(self, mocker):
        mocker.patch(
            "src.speech_output.Path.exists",
            return_value=False,
        )
        result = check_kokoro_files()
        assert result is not None
        assert "kokoro-v1.0.onnx" in result
        assert "voices-v1.0.bin" in result

    def test_returns_warning_when_one_file_missing(self, mocker):
        mocker.patch(
            "src.speech_output.Path.exists",
            side_effect=[True, False],
        )
        result = check_kokoro_files()
        assert result is not None
        assert "TTS will be unavailable" in result

    def test_warning_mentions_missing_filename(self, mocker):
        mocker.patch(
            "src.speech_output.Path.exists",
            side_effect=[False, True],
        )
        result = check_kokoro_files()
        assert "kokoro-v1.0.onnx" in result
