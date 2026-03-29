"""Orchestrator that routes queries to Ollama or Claude via OpenRouter.

Composes OllamaRouter for complexity classification, OpenRouterClient for
Claude responses, and a direct Ollama client for simple queries.
"""

import ollama

from src.openrouter_client import (
    OPUS_DISPLAY_NAME,
    SONNET_DISPLAY_NAME,
    OpenRouterClient,
)
from src.router import OLLAMA_MODEL, OllamaRouter


class Orchestrator:
    """Routes user queries to the appropriate LLM backend.

    Uses OllamaRouter to classify each query, then dispatches to a local
    Ollama model for simple queries or to Claude Sonnet/Opus via
    OpenRouter for complex ones.

    Args:
        ollama_model: The Ollama model name used for both classification
          and simple-query responses.  Defaults to OLLAMA_MODEL.

    Attributes:
        last_backend: Human-readable label of the backend that answered
          the most recent query (e.g. ``"Ollama: deepseek-r1-..."``).
    """

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
        """Generate a response and update the conversation history.

        Classifies the query, dispatches to the appropriate backend, and
        appends the user message and assistant response to the history.

        Args:
            query: The user's input text.
            history: The current conversation history as a list of
              ``{"role": ..., "content": ...}`` dicts.

        Returns:
            A tuple of ``(response_text, updated_history)`` where
            ``updated_history`` includes the new user and assistant turns.
        """
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
