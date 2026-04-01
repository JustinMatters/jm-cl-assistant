"""Text-to-speech synthesis using the kokoro-onnx model."""

from pathlib import Path

import numpy as np
from kokoro_onnx import Kokoro


def check_kokoro_files(
    model_path: str = "kokoro-v1.0.onnx",
    voices_path: str = "voices-v1.0.bin",
) -> str | None:
    """Check that the Kokoro model files exist in the working directory.

    Args:
        model_path: Expected path to the ONNX model file.
        voices_path: Expected path to the voices binary file.

    Returns:
        A warning string listing any missing files, or ``None`` if both
        files are present.
    """
    missing = [p for p in (model_path, voices_path) if not Path(p).exists()]
    if missing:
        return (
            "Kokoro model files not found — TTS will be unavailable. "
            f"Missing: {', '.join(missing)}"
        )
    return None


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
            try:
                self._model = Kokoro(self.model_path, self.voices_path)
            except FileNotFoundError as exc:
                raise FileNotFoundError(
                    f"Kokoro model files not found ({exc}) — "
                    "download kokoro-v1.0.onnx and voices-v1.0.bin "
                    "to the project root"
                ) from exc
            except Exception as exc:
                raise RuntimeError(
                    f"Kokoro model failed to load: {exc}"
                ) from exc
        audio, sample_rate = self._model.create(
            text, voice=voice or self.voice, speed=self.speed
        )
        return audio, int(sample_rate)
