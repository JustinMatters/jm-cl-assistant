import ollama

from src.claude_client import ClaudeClient
from src.router import OLLAMA_MODEL, OllamaRouter


class Orchestrator:
    def __init__(self) -> None:
        self._router = OllamaRouter()
        self._claude = ClaudeClient()

    def respond(self, query: str, history: list) -> tuple[str, list]:
        classification = self._router.classify(query)
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
        result = ollama.chat(model=OLLAMA_MODEL, messages=messages)
        return result["message"]["content"]
