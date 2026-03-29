import ollama

from src.openrouter_client import (
    OPUS_DISPLAY_NAME,
    SONNET_DISPLAY_NAME,
    OpenRouterClient,
)
from src.router import OLLAMA_MODEL, OllamaRouter


class Orchestrator:
    def __init__(self, ollama_model: str = OLLAMA_MODEL) -> None:
        self._router = OllamaRouter(model=ollama_model)
        self._claude = OpenRouterClient()
        self.last_backend: str = ""
        self._backend_labels = {
            "simple": f"Ollama: {ollama_model.split('/')[-1]}",
            "complex_sonnet": f"OpenRouter: {SONNET_DISPLAY_NAME}",
            "complex_opus": f"OpenRouter: {OPUS_DISPLAY_NAME}",
        }

    def respond(self, query: str, history: list) -> tuple[str, list]:
        classification = self._router.classify(query)
        self.last_backend = self._backend_labels[classification]
        if classification == "simple":
            response = self._ollama_respond(query, history)
        elif classification == "complex_sonnet":
            response = self._claude.ask(query, "sonnet", history)
        else:
            response = self._claude.ask(query, "opus", history)
        updated_history = list(history) + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": response},
        ]
        return response, updated_history

    def _ollama_respond(self, query: str, history: list) -> str:
        messages = list(history) + [{"role": "user", "content": query}]
        result = ollama.chat(model=self._router._model, messages=messages)
        return result["message"]["content"]
