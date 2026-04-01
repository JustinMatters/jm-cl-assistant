"""Speech-to-text transcription using the OpenAI Whisper model."""

import numpy as np
import scipy.signal
import whisper

WHISPER_MODEL = "medium"
_WHISPER_SR = 16_000  # Whisper always expects 16 kHz input
# Segments whose average no_speech_prob exceeds this are treated as silence.
# 0.0 = definitely speech, 1.0 = definitely no speech.
_NO_SPEECH_THRESHOLD = 0.6


class WhisperTranscriber:
    """Transcribes audio to text using a local Whisper model.

    The Whisper model is loaded lazily on the first call to ``transcribe``
    to avoid startup delay when STT is not needed.

    Args:
        model: Whisper model size to load (e.g. ``"tiny"``, ``"base"``,
          ``"medium"``).  Defaults to WHISPER_MODEL (``"medium"``).
    """

    def __init__(self, model: str = WHISPER_MODEL) -> None:
        self._model_name = model
        self._model = None  # loaded lazily on first transcribe() call

    def transcribe(self, audio_array: np.ndarray, sample_rate: int) -> str:
        """Transcribe a raw audio array to text.

        Loads the Whisper model on the first call, then reuses it for
        subsequent calls.  Resamples the audio to 16 kHz if necessary —
        Whisper always expects 16 kHz input regardless of the original
        capture sample rate.

        Args:
            audio_array: Float32 numpy array of audio samples normalised
              to the range [-1, 1].
            sample_rate: Sample rate of the audio in Hz (e.g. 44100 or
              48000 from a browser microphone).

        Returns:
            The transcribed text as a string.  Returns an empty string
            for silent or unintelligible audio.

        Raises:
            RuntimeError: If the Whisper model fails to load.
            Exception: If transcription fails due to invalid audio or an
              internal Whisper error.
        """
        if self._model is None:
            self._model = whisper.load_model(self._model_name)
        if sample_rate != _WHISPER_SR:
            num_samples = round(len(audio_array) * _WHISPER_SR / sample_rate)
            audio_array = scipy.signal.resample(audio_array, num_samples)
        result = self._model.transcribe(audio_array)
        segments = result.get("segments", [])
        if segments:
            avg_no_speech = sum(s["no_speech_prob"] for s in segments) / len(
                segments
            )
            if avg_no_speech > _NO_SPEECH_THRESHOLD:
                return ""
        return result["text"]
