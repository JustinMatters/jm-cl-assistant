"""Orchestrator that routes queries to Ollama or Claude via OpenRouter.

Composes OllamaRouter for complexity classification, OpenRouterClient for
Claude responses, and a direct Ollama client for trivial and simple queries.
"""

import ollama

from src.openrouter_client import (
    OPUS_DISPLAY_NAME,
    SONNET_DISPLAY_NAME,
    OpenRouterClient,
)
from src.router import OLLAMA_FAST_MODEL, OLLAMA_MODEL, OllamaRouter


class Orchestrator:
    """Routes user queries to the appropriate LLM backend.

    Uses OllamaRouter to classify each query, then dispatches to a fast
    local Ollama model for trivial queries, a larger local model for simple
    queries, or to Claude Sonnet/Opus via OpenRouter for complex ones.

    Args:
        ollama_model: The Ollama model name used for classification and
          simple-query responses.  Defaults to OLLAMA_MODEL.
        fast_model: The Ollama model name used for trivial queries.
          Defaults to OLLAMA_FAST_MODEL.

    Attributes:
        last_backend: Human-readable label of the backend that answered
          the most recent query (e.g. ``"Ollama: qwen3:1.7b"``).
    """

    def __init__(
        self,
        ollama_model: str = OLLAMA_MODEL,
        fast_model: str = OLLAMA_FAST_MODEL,
    ) -> None:
        self._router = OllamaRouter(model=ollama_model)
        self._claude = OpenRouterClient()
        self._fast_model = fast_model
        self.last_backend: str = ""
        self._backend_labels = {
            "trivial_ollama": f"Ollama: {fast_model.split('/')[-1]}",
            "simple_ollama": f"Ollama: {ollama_model.split('/')[-1]}",
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
        if classification == "trivial_ollama":
            response = self._ollama_respond(query, history, self._fast_model)
        elif classification == "simple_ollama":
            response = self._ollama_respond(query, history, self._router._model)
        elif classification == "complex_sonnet":
            response = self._claude.ask(query, "sonnet", history)
        else:
            response = self._claude.ask(query, "opus", history)
        updated_history = list(history) + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": response},
        ]
        return response, updated_history

    def _ollama_respond(self, query: str, history: list, model: str) -> str:
        """Send a query to a local Ollama model and return the response.

        Args:
            query: The user's input text.
            history: Conversation history as a list of message dicts.
            model: The Ollama model name to call.

        Returns:
            The model's response text.
        """
        messages = list(history) + [{"role": "user", "content": query}]
        result = ollama.chat(model=model, messages=messages)
        return result["message"]["content"]
