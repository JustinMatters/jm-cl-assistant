"""Orchestrator that routes queries to Ollama or Claude via OpenRouter.

Composes OllamaRouter for complexity classification, OpenRouterClient for
Claude responses, and a direct Ollama client for trivial and simple queries.
"""

import inspect
import json
import logging
from collections.abc import Iterator
from uuid import uuid4

import ollama

from src.memory.store import MemoryStore
from src.model_config import load_models
from src.openrouter_client import (
    OPUS_DISPLAY_NAME,
    SONNET_DISPLAY_NAME,
    OpenRouterClient,
)
from src.router import OLLAMA_FAST_MODEL, OLLAMA_MODEL, OllamaRouter
from src.tools.image_utils import decode_image, is_image_sentinel
from src.tools.registry import REGISTRY

# Load model config once at module level so all Orchestrator instances
# share the same configuration without re-reading the file.
_MODEL_CONFIG = load_models()

# Base-name prefixes (e.g. "gemma4") extracted from all vision-capable
# Ollama model entries in the config.  A queried model is considered
# vision-capable if its base name starts with any of these prefixes.
_OLLAMA_VISION_PREFIXES: frozenset[str] = frozenset(
    cfg.model_id.lower().split("/")[-1].split(":")[0]
    for cfg in _MODEL_CONFIG.values()
    if cfg.provider == "ollama" and cfg.vision
)


def _model_supports_vision(model_name: str) -> bool:
    """Return True if model_name is a vision-capable Ollama model per config.

    Matches by extracting the base name (stripping namespace and tag) and
    checking whether it starts with any prefix derived from the configured
    vision-capable Ollama models.  For example, if ``gemma4:e4b`` is
    configured with ``vision: true``, then ``google/gemma4:12b`` also
    matches.
    """
    base = model_name.lower().split("/")[-1].split(":")[0]
    return any(base.startswith(p) for p in _OLLAMA_VISION_PREFIXES)


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
        self._pending_execution: dict | None = None
        self._pending_image = None
        self._backend_labels = {
            "trivial_llm": f"Ollama: {fast_model.split('/')[-1]}",
            "simple_llm": f"Ollama: {ollama_model.split('/')[-1]}",
            "advanced_llm": f"OpenRouter: {SONNET_DISPLAY_NAME}",
            "complex_llm": f"OpenRouter: {OPUS_DISPLAY_NAME}",
        }

    def respond(
        self,
        query: str,
        history: list,
        memory_enabled: bool = True,
        enabled_tools: set[str] | None = None,
        image=None,
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
            enabled_tools: Set of tool names currently active in the UI.
              When provided, overrides the registry's ``default_enabled``
              flags so the UI state is honoured.  Pass ``None`` to fall
              back to per-tool defaults (used in tests and CLI mode).

        Returns:
            A tuple of ``(response_text, updated_history)`` where
            ``updated_history`` includes the new user and assistant turns.
        """
        self._pending_image = None
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
        # Build the active tool set for this turn.
        # Use UI-provided set when available; fall back to registry defaults.
        if enabled_tools is not None:
            active_names = enabled_tools
        else:
            active_names = {t.name for t in REGISTRY.all() if t.default_enabled}

        classification = self._router.classify(query, active_names)

        # Attempt tool dispatch — covers all registered Approach A tiers.
        # dispatch() returns None if the tool cannot handle the query or is
        # gated by min_tier; orchestrator then falls back to an LLM tier.
        tool_result = REGISTRY.dispatch(
            classification,
            query,
            active_names,
            classification,
            store=self._memory if memory_enabled else None,
        )
        if tool_result is not None:
            matched = next(
                (
                    t
                    for t in REGISTRY.enabled_tools(active_names)
                    if t.router_tier == classification
                ),
                None,
            )
            self.last_backend = matched.label if matched else classification
            response = tool_result
        else:
            # LLM tier, or a tool tier whose tool returned None (fall back).
            effective = (
                classification
                if classification in self._backend_labels
                else "trivial_llm"
            )
            # When an image is attached and the selected Ollama model does
            # not support vision, escalate to Claude Sonnet which does.
            if image is not None and effective in (
                "trivial_llm",
                "simple_llm",
            ):
                ollama_model = (
                    self._fast_model
                    if effective == "trivial_llm"
                    else self._ollama_model
                )
                if not _model_supports_vision(ollama_model):
                    effective = "advanced_llm"
            self.last_backend = self._backend_labels[effective]
            b_schemas = REGISTRY.schemas(active_names)
            b_executor = (
                self._make_b_executor(active_names) if b_schemas else None
            )
            if effective == "trivial_llm":
                response = self._ollama_respond(
                    query,
                    augmented,
                    self._fast_model,
                    tools=b_schemas,
                    tool_executor=b_executor,
                    image=image,
                )
            elif effective == "simple_llm":
                response = self._ollama_respond(
                    query,
                    augmented,
                    self._ollama_model,
                    tools=b_schemas,
                    tool_executor=b_executor,
                    image=image,
                )
            elif effective == "advanced_llm":
                response = self._claude.ask(
                    query,
                    "sonnet",
                    augmented,
                    tools=b_schemas or None,
                    tool_executor=b_executor,
                    image=image,
                )
            else:
                response = self._claude.ask(
                    query,
                    "opus",
                    augmented,
                    tools=b_schemas or None,
                    tool_executor=b_executor,
                    image=image,
                )
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

    def _make_b_executor(self, active_names: set[str]):
        """Return a tool executor for Approach B (LLM function-calling) tools.

        The returned callable looks up the tool by name in the registry,
        normalises ``arguments`` to a JSON string (Ollama passes a dict;
        OpenRouter passes a string), and calls the tool's ``callable``.

        Args:
            active_names: Set of tool names currently enabled.

        Returns:
            A ``(name, arguments) -> str`` callable suitable for passing
            to ``OpenRouterClient.ask()`` or ``_ollama_respond()``.
        """

        session_id = self.session_id
        orchestrator = self

        def _execute(name: str, arguments: str | dict) -> str:
            tools = REGISTRY.enabled_tools(active_names)
            tool = next((t for t in tools if t.name == name), None)
            if tool is None:
                return f"Error: unknown tool {name!r}"
            args_str = (
                json.dumps(arguments)
                if isinstance(arguments, dict)
                else arguments
            )
            if tool.requires_confirmation:
                # Store pending execution for the UI to surface a modal.
                try:
                    code = json.loads(args_str).get("code", "")
                except Exception:
                    code = args_str
                orchestrator._pending_execution = {
                    "tool": tool,
                    "args_str": args_str,
                    "code": code,
                }
                return (
                    "Code execution requires user approval. "
                    "The user has been shown the code and must "
                    "approve before it can run."
                )
            try:
                sig = inspect.signature(tool.callable)
                kwargs: dict = {}
                if "session_id" in sig.parameters:
                    kwargs["session_id"] = session_id
                result = tool.callable(args_str, **kwargs)
                if result is None:
                    return f"Error: {name} returned no result"
                if is_image_sentinel(result):
                    orchestrator._pending_image = decode_image(result)
                    return "Image generated successfully."
                return result
            except Exception as exc:
                return f"Error executing {name}: {exc}"

        return _execute

    def confirm_pending(self) -> str:
        """Execute the stored pending code and clear the pending state.

        Returns:
            The code's output, or an error string if execution fails.
        """
        if self._pending_execution is None:
            return "No pending code execution."
        tool = self._pending_execution["tool"]
        args_str = self._pending_execution["args_str"]
        self._pending_execution = None
        try:
            result = tool.callable(args_str)
            return result if result is not None else "(no output)"
        except Exception as exc:
            return f"Execution error: {exc}"

    def cancel_pending(self) -> str:
        """Discard the stored pending code without executing it.

        Returns:
            A cancellation confirmation string.
        """
        self._pending_execution = None
        return "Code execution cancelled."

    def _ollama_respond(
        self,
        query: str,
        history: list,
        model: str,
        tools: list[dict] | None = None,
        tool_executor=None,
        max_tool_iterations: int = 5,
        image=None,
    ) -> str:
        """Send a query to a local Ollama model and return the response.

        When ``tools`` and ``tool_executor`` are provided, runs an
        agentic loop matching the Ollama native tool-calling protocol
        (arguments arrive as a Python dict, not a JSON string).

        Args:
            query: The user's input text.
            history: Conversation history as a list of message dicts.
            model: The Ollama model name to call.
            tools: OpenAI-compatible tool schemas to pass to the model.
              ``None`` or ``[]`` disables tool calling.
            tool_executor: Callable invoked as
              ``tool_executor(name, arguments)`` where ``arguments`` is
              a Python dict from the Ollama response.
            max_tool_iterations: Maximum tool-call rounds before the
              loop is terminated with a guard message.

        Returns:
            The model's response text.
        """
        user_msg: dict = {"role": "user", "content": query}
        if image is not None:
            import base64
            import io

            buf = io.BytesIO()
            image.save(buf, format="PNG")
            user_msg["images"] = [base64.b64encode(buf.getvalue()).decode()]
        messages = list(history) + [user_msg]
        tool_rounds = 0
        while True:
            try:
                chat_kwargs: dict = {"model": model, "messages": messages}
                if tools:
                    chat_kwargs["tools"] = tools
                result = ollama.chat(**chat_kwargs)
            except Exception as exc:
                return f"(Ollama error: {exc} — please check it is running)"

            msg = result["message"]
            tool_calls = msg.get("tool_calls")

            if not tool_calls or not tools or not tool_executor:
                return msg.get("content") or ""

            # Append assistant message and execute each tool call.
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.get("content") or "",
                    "tool_calls": [
                        {
                            "function": {
                                "name": c["function"]["name"],
                                "arguments": c["function"]["arguments"],
                            }
                        }
                        for c in tool_calls
                    ],
                }
            )
            for call in tool_calls:
                fn = call["function"]
                result_str = tool_executor(fn["name"], fn["arguments"])
                messages.append({"role": "tool", "content": result_str})

            tool_rounds += 1
            if tool_rounds >= max_tool_iterations:
                return (
                    f"(Tool loop reached {max_tool_iterations} iterations"
                    " without a final response)"
                )

    def _ollama_stream(
        self,
        query: str,
        history: list,
        model: str,
        image=None,
    ) -> Iterator[str]:
        """Stream content chunks from a local Ollama model.

        Does not support tool calling — use ``_ollama_respond`` for
        Approach B agentic paths that require full response inspection.

        Args:
            query: The user's input text.
            history: Conversation history as a list of message dicts.
            model: The Ollama model name to call.
            image: Optional PIL Image encoded as base64 PNG image data.

        Yields:
            Content string chunks as they arrive from the Ollama stream.
        """
        user_msg: dict = {"role": "user", "content": query}
        if image is not None:
            import base64
            import io

            buf = io.BytesIO()
            image.save(buf, format="PNG")
            user_msg["images"] = [base64.b64encode(buf.getvalue()).decode()]
        messages = list(history) + [user_msg]
        try:
            stream = ollama.chat(model=model, messages=messages, stream=True)
            for chunk in stream:
                content = chunk["message"]["content"]
                if content:
                    yield content
        except Exception as exc:
            yield (f"(Ollama error: {exc} — please check it is running)")

    def stream_respond(
        self,
        query: str,
        history: list,
        memory_enabled: bool = True,
        enabled_tools: set[str] | None = None,
        image=None,
    ) -> Iterator[tuple[str, list | None]]:
        """Generate a streaming response, yielding incremental chunks.

        Yields ``(partial_text, None)`` for intermediate chunks during
        LLM streaming and a final ``(full_text, updated_history)`` on
        completion.  Approach A tool results and Approach B agentic
        loops are not streamed — they produce a single final yield.

        Args:
            query: The user's input text.
            history: Current conversation history.
            memory_enabled: When ``False``, memory reads/writes are
              skipped for this call.
            enabled_tools: Set of tool names currently active in the UI.
              ``None`` falls back to per-tool ``default_enabled`` flags.
            image: Optional PIL Image attached to the query.

        Yields:
            ``(text, updated_history_or_none)`` where
            ``updated_history_or_none`` is ``None`` for intermediate
            chunks and the updated history list for the final yield.
        """
        self._pending_image = None
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
        if enabled_tools is not None:
            active_names = enabled_tools
        else:
            active_names = {t.name for t in REGISTRY.all() if t.default_enabled}

        classification = self._router.classify(query, active_names)

        tool_result = REGISTRY.dispatch(
            classification,
            query,
            active_names,
            classification,
            store=self._memory if memory_enabled else None,
        )
        if tool_result is not None:
            matched = next(
                (
                    t
                    for t in REGISTRY.enabled_tools(active_names)
                    if t.router_tier == classification
                ),
                None,
            )
            self.last_backend = matched.label if matched else classification
            response = tool_result
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
            yield response, updated_history
            return

        effective = (
            classification
            if classification in self._backend_labels
            else "trivial_llm"
        )
        if image is not None and effective in (
            "trivial_llm",
            "simple_llm",
        ):
            ollama_model = (
                self._fast_model
                if effective == "trivial_llm"
                else self._ollama_model
            )
            if not _model_supports_vision(ollama_model):
                effective = "advanced_llm"
        self.last_backend = self._backend_labels[effective]
        b_schemas = REGISTRY.schemas(active_names)

        if b_schemas:
            # Approach B tool loop — run synchronously, yield final only.
            b_executor = self._make_b_executor(active_names)
            if effective == "trivial_llm":
                response = self._ollama_respond(
                    query,
                    augmented,
                    self._fast_model,
                    tools=b_schemas,
                    tool_executor=b_executor,
                    image=image,
                )
            elif effective == "simple_llm":
                response = self._ollama_respond(
                    query,
                    augmented,
                    self._ollama_model,
                    tools=b_schemas,
                    tool_executor=b_executor,
                    image=image,
                )
            elif effective == "advanced_llm":
                response = self._claude.ask(
                    query,
                    "sonnet",
                    augmented,
                    tools=b_schemas,
                    tool_executor=b_executor,
                    image=image,
                )
            else:
                response = self._claude.ask(
                    query,
                    "opus",
                    augmented,
                    tools=b_schemas,
                    tool_executor=b_executor,
                    image=image,
                )
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
            yield response, updated_history
            return

        # No Approach B tools — stream the response.
        if effective == "trivial_llm":
            stream: Iterator[str] = self._ollama_stream(
                query, augmented, self._fast_model, image=image
            )
        elif effective == "simple_llm":
            stream = self._ollama_stream(
                query, augmented, self._ollama_model, image=image
            )
        elif effective == "advanced_llm":
            stream = self._claude.stream_ask(
                query, "sonnet", augmented, image=image
            )
        else:
            stream = self._claude.stream_ask(
                query, "opus", augmented, image=image
            )

        accumulated = ""
        for chunk in stream:
            accumulated += chunk
            yield accumulated, None

        response = accumulated
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
        yield response, updated_history
