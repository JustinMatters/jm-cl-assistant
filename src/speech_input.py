"""Speech-to-text transcription using the OpenAI Whisper model."""

import numpy as np
import whisper

WHISPER_MODEL = "medium"


class WhisperTranscriber:
    """Transcribes audio to text using a local Whisper model.

    Args:
        model: Whisper model size to load (e.g. ``"tiny"``, ``"base"``,
          ``"medium"``).  Defaults to WHISPER_MODEL (``"medium"``).
    """

    def __init__(self, model: str = WHISPER_MODEL) -> None:
        self._model = whisper.load_model(model)

    def transcribe(self, audio_array: np.ndarray, sample_rate: int) -> str:
        """Transcribe a raw audio array to text.

        Args:
            audio_array: Float32 numpy array of audio samples normalised
              to the range [-1, 1].
            sample_rate: Sample rate of the audio in Hz.

        Returns:
            The transcribed text as a string.  Returns an empty string
            for silent or unintelligible audio.
        """
        result = self._model.transcribe(audio_array)
        return result["text"]
