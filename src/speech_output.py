"""Text-to-speech synthesis using the kokoro-onnx model."""

import numpy as np
from kokoro_onnx import Kokoro


class KokoroSpeaker:
    """Synthesises speech from text using the Kokoro ONNX TTS model.

    The Kokoro model is loaded lazily on the first call to ``synthesize``
    to avoid startup delay when TTS is not needed.

    Args:
        model_path: Path to the Kokoro ONNX model file.
        voices_path: Path to the Kokoro voices binary file.
        voice: Voice identifier to use for synthesis (e.g. ``"af_heart"``).
        speed: Speech speed multiplier (1.0 = normal).

    Attributes:
        model_path: Path to the ONNX model file.
        voices_path: Path to the voices binary file.
        voice: Active voice identifier.
        speed: Speech speed multiplier.
    """

    def __init__(
        self,
        model_path: str = "kokoro-v1.0.onnx",
        voices_path: str = "voices-v1.0.bin",
        voice: str = "af_heart",
        speed: float = 1.0,
    ) -> None:
        self.model_path = model_path
        self.voices_path = voices_path
        self.voice = voice
        self.speed = speed
        self._model = None

    def synthesize(
        self, text: str, voice: str | None = None
    ) -> tuple[np.ndarray, int]:
        """Convert text to speech audio.

        Loads the Kokoro model on the first call, then reuses it for
        subsequent calls.

        Args:
            text: The text to synthesise.
            voice: Voice ID to use for this call. Overrides the instance
              default when provided.

        Returns:
            A tuple of ``(audio_array, sample_rate)`` where
            ``audio_array`` is a float32 numpy array of audio samples
            and ``sample_rate`` is the sample rate in Hz.
        """
        if self._model is None:
            self._model = Kokoro(self.model_path, self.voices_path)
        audio, sample_rate = self._model.create(
            text, voice=voice or self.voice, speed=self.speed
        )
        return audio, int(sample_rate)
