import numpy as np
import whisper

WHISPER_MODEL = "medium"


class WhisperTranscriber:
    def __init__(self) -> None:
        self._model = whisper.load_model(WHISPER_MODEL)

    def transcribe(self, audio_array: np.ndarray, sample_rate: int) -> str:
        result = self._model.transcribe(audio_array)
        return result["text"]
