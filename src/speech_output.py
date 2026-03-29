import numpy as np
from kokoro_onnx import Kokoro


class KokoroSpeaker:
    def __init__(self) -> None:
        self._model = None

    def synthesize(self, text: str) -> tuple[np.ndarray, int]:
        if self._model is None:
            self._model = Kokoro()
        audio, sample_rate = self._model.create(text)
        return audio, int(sample_rate)
