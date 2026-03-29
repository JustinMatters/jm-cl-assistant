"""Text-to-speech synthesis using the kokoro-onnx model."""

import numpy as np
from kokoro_onnx import Kokoro


class KokoroSpeaker:
    """Synthesises speech from text using the Kokoro ONNX TTS model.

    The Kokoro model is loaded lazily on the first call to ``synthesize``
    to avoid startup delay when TTS is not needed.
    """

    def __init__(self) -> None:
        self._model = None

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        """Convert text to speech audio.

        Loads the Kokoro model on the first call, then reuses it for
        subsequent calls.

        Args:
            text: The text to synthesise.

        Returns:
            A tuple of ``(audio_array, sample_rate)`` where
            ``audio_array`` is a float32 numpy array of audio samples
            and ``sample_rate`` is the sample rate in Hz.
        """
        if self._model is None:
            self._model = Kokoro()
        audio, sample_rate = self._model.create(text)
        return audio, int(sample_rate)
