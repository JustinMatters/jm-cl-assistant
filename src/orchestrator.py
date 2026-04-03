"""Orchestrator that routes queries to Ollama or Claude via OpenRouter.

Composes OllamaRouter for complexity classification, OpenRouterClient for
Claude responses, and a direct Ollama client for trivial and simple queries.
"""

import logging
import re
from uuid import uuid4

import ollama

from src.memory.store import MemoryStore
from src.openrouter_client import (
    OPUS_DISPLAY_NAME,
    SONNET_DISPLAY_NAME,
    OpenRouterClient,
)
from src.router import OLLAMA_FAST_MODEL, OLLAMA_MODEL, OllamaRouter
from src.tools.calculator import calculate

_MATHS_PREAMBLE = re.compile(
    r"^\s*(?:what(?:'s|\s+is)?\s+|"
    r"calculate\s+|compute\s+|evaluate\s+|"
    r"solve\s+|find\s+|work\s+out\s+)",
    re.IGNORECASE,
)


class Orchestrator:
    """Routes user queries to the appropriate LLM backend.

    Uses OllamaRouter to classify each query, then dispatches to a fast
    local Ollama model for trivial queries, a larger local model for simple
    queries, or to Claude Sonnet/Opus via OpenRouter for complex ones.

    Args:
        ollama_model: The Ollama model name used for simple-query responses.
          Defaults to OLLAMA_MODEL.
        fast_model: The Ollama model name used for routing/classification
          and trivial-query responses.  Defaults to OLLAMA_FAST_MODEL.
        session_id: UUID string identifying this app session. Used as
          metadata on every memory write. Defaults to a fresh UUID so
          existing callers that omit it continue to work.
        memory_enabled: When False, the memory store is not initialised
          and no reads or writes occur. Useful in tests and when the
          user disables memory via the UI toggle.

    Attributes:
        last_backend: Human-readable label of the backend that answered
          the most recent query (e.g. ``"Ollama: qwen3:1.7b"``).
        session_id: The session identifier passed at construction.
    """

    def __init__(
        self,
        ollama_model: str = OLLAMA_MODEL,
        fast_model: str = OLLAMA_FAST_MODEL,
        session_id: str = "",
        memory_enabled: bool = True,
    ) -> None:
        self._router = OllamaRouter(model=fast_model)
        self._claude = OpenRouterClient()
        self._fast_model = fast_model
        self._ollama_model = ollama_model
        self.session_id: str = session_id or uuid4().hex
        self.last_backend: str = "(awaiting first query)"
        self._memory: MemoryStore | None = None
        if memory_enabled:
            try:
                self._memory = MemoryStore()
            except Exception as exc:
                logging.warning(
                    "Memory store failed to initialise (%s); "
                    "continuing without memory",
                    exc,
                )
        self._backend_labels = {
            "trivial_ollama": f"Ollama: {fast_model.split('/')[-1]}",
            "simple_ollama": f"Ollama: {ollama_model.split('/')[-1]}",
            "complex_sonnet": f"OpenRouter: {SONNET_DISPLAY_NAME}",
            "complex_opus": f"OpenRouter: {OPUS_DISPLAY_NAME}",
            "maths": "Tool: calculator",
        }

    def respond(
        self,
        query: str,
        history: list,
        memory_enabled: bool = True,
    ) -> tuple[str, list]:
        """Generate a response and update the conversation history.

        Classifies the query, dispatches to the appropriate backend, and
        appends the user message and assistant response to the history.

        Args:
            query: The user's input text.
            history: The current conversation history as a list of
              ``{"role": ..., "content": ...}`` dicts.
            memory_enabled: When False, the memory store is neither read
              from (no context injection) nor written to (no recording)
              for this call. Allows the user to toggle memory mid-session.

        Returns:
            A tuple of ``(response_text, updated_history)`` where
            ``updated_history`` includes the new user and assistant turns.
        """
        # Retrieve relevant past memories and inject as a system message.
        # augmented is a local copy — it is never written back to history,
        # so the injected context does not accumulate across turns.
        context_block = ""
        if self._memory is not None and memory_enabled and query.strip():
            try:
                context_block = self._memory.get_context_block(query)
            except Exception as exc:
                logging.warning("Memory context retrieval failed: %s", exc)
        augmented = (
            [{"role": "system", "content": context_block}] + list(history)
            if context_block
            else list(history)
        )
        classification = self._router.classify(query)
        self.last_backend = self._backend_labels[classification]
        if classification == "maths":
            expression = _MATHS_PREAMBLE.sub("", query).rstrip("?").strip()
            result = calculate(expression)
            if result.startswith("Error:"):
                # Expression could not be parsed — fall back to fast Ollama
                self.last_backend = self._backend_labels["trivial_ollama"]
                response = self._ollama_respond(
                    query, augmented, self._fast_model
                )
            else:
                response = result
        elif classification == "trivial_ollama":
            response = self._ollama_respond(query, augmented, self._fast_model)
        elif classification == "simple_ollama":
            response = self._ollama_respond(
                query, augmented, self._ollama_model
            )
        elif classification == "complex_sonnet":
            response = self._claude.ask(query, "sonnet", augmented)
        else:
            response = self._claude.ask(query, "opus", augmented)
        updated_history = list(history) + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": response},
        ]
        if self._memory is not None and memory_enabled:
            try:
                self._memory.add(
                    f"User: {query}\nAssistant: {response}",
                    source="conversation",
                    session_id=self.session_id,
                )
            except Exception as exc:
                logging.warning("Memory write failed: %s", exc)
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
        try:
            result = ollama.chat(model=model, messages=messages)
            return result["message"]["content"]
        except Exception as exc:
            return f"(Ollama error: {exc} — please check it is running)"
