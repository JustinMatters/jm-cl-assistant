import numpy as np
import pytest

speech_input_module = pytest.importorskip("src.speech_input")
speech_output_module = pytest.importorskip("src.speech_output")
WhisperTranscriber = speech_input_module.WhisperTranscriber
KokoroSpeaker = speech_output_module.KokoroSpeaker


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
        WhisperTranscriber()
        mock_load.assert_called_once_with("medium")

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
