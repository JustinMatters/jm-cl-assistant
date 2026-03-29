import ollama

from src.claude_client import ClaudeClient
from src.router import OLLAMA_MODEL, OllamaRouter

_BACKEND_LABELS = {
    "simple": "Ollama",
    "complex_sonnet": "Claude Sonnet",
    "complex_opus": "Claude Opus",
}


class Orchestrator:
    def __init__(self, ollama_model: str = OLLAMA_MODEL) -> None:
        self._router = OllamaRouter(model=ollama_model)
        self._claude = ClaudeClient()
        self.last_backend: str = ""

    def respond(self, query: str, history: list) -> tuple[str, list]:
        classification = self._router.classify(query)
        self.last_backend = _BACKEND_LABELS[classification]
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
