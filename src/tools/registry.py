"""Tool registry and metadata protocol for the jm-cl-assistant application.

Provides ``ToolDefinition`` (a dataclass carrying all metadata for a single
runtime tool) and ``ToolRegistry`` (a runtime catalogue that maps tier tokens
to tools and drives routing, UI display, and LLM function-calling schemas).

All tool modules register with the global ``REGISTRY`` singleton at import
time; ``src/tools/__init__.py`` imports every tool module so the registry is
fully populated as soon as any code imports from this package.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.memory.store import MemoryStore

# Rank table used to enforce min_tier at dispatch time.
# Tool tiers (e.g. "maths", "convert") are absent from this table;
# _TIER_RANK.get() defaults to 0 for unknown keys, making all Approach A
# tools with min_tier="trivial_ollama" (rank 0) always reachable.
_TIER_RANK: dict[str, int] = {
    "trivial_ollama": 0,
    "simple_ollama": 1,
    "complex_sonnet": 2,
    "complex_opus": 3,
}


@dataclass
class ToolDefinition:
    """Metadata and callable for a single runtime tool.

    Carries all information needed for routing (``router_tier``,
    ``description``, ``examples``), UI display (``label``,
    ``default_enabled``, ``category``), capability gating (``min_tier``),
    and LLM function calling (``parameters_schema`` for Approach B tools).

    Args:
        name: Machine identifier used as the registry key,
          e.g. ``"calculator"``.
        router_tier: Classification token produced by the router when
          this tool should be invoked, e.g. ``"maths"``.
        label: Human-readable backend indicator shown in the UI,
          e.g. ``"Tool: calculator"``.
        description: Natural language description of the queries this
          tool handles.  Used verbatim in the router system prompt.
        examples: Sample queries used in the router system prompt.
        default_enabled: Whether the tool is active before the user
          changes any UI toggle.
        min_tier: Minimum route tier required to invoke this tool.
          One of ``trivial_ollama``, ``simple_ollama``,
          ``complex_sonnet``, ``complex_opus``.
        approach: ``"A"`` for router-dispatched (direct callable) or
          ``"B"`` for LLM function calling.
        callable: Function called with the raw query string; returns a
          result string or ``None`` to signal the query cannot be
          handled (orchestrator falls back to LLM).
        category: Short label for grouping tools in the UI accordion,
          e.g. ``"maths"``, ``"web"``, ``"system"``.
        is_async: ``True`` if ``callable`` is a coroutine that must be
          awaited.
        parameters_schema: OpenAI-compatible JSON schema for Approach B
          tools; ``None`` for Approach A tools.
    """

    name: str
    router_tier: str
    label: str
    description: str
    examples: list[str]
    default_enabled: bool
    min_tier: str
    approach: str
    callable: Callable[..., str | None]
    category: str = "general"
    is_async: bool = False
    parameters_schema: dict | None = None


class ToolRegistry:
    """Runtime catalogue of registered tools.

    Tools self-register at import time by calling ``register()`` on the
    global ``REGISTRY`` singleton.  The registry is consulted by the
    orchestrator and router to build the active tool set for each turn.

    The active set is always constructed fresh per turn (never mutated)
    by filtering with ``enabled_tools()`` or ``dispatch()``.
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, defn: ToolDefinition) -> None:
        """Register a tool definition.

        Args:
            defn: The ``ToolDefinition`` to register.  A tool with the
              same ``name`` replaces any previous registration.
        """
        self._tools[defn.name] = defn

    def all(self) -> list[ToolDefinition]:
        """Return all registered tool definitions.

        Returns:
            All ``ToolDefinition`` instances in registration order.
        """
        return list(self._tools.values())

    def enabled_tools(self, enabled_names: set[str]) -> list[ToolDefinition]:
        """Return definitions for the enabled subset of registered tools.

        Args:
            enabled_names: Set of tool names currently enabled (from UI
              state or ``default_enabled`` flags).

        Returns:
            Definitions whose ``name`` is in ``enabled_names``.
        """
        return [t for t in self._tools.values() if t.name in enabled_names]

    def router_prompt_section(self, enabled_names: set[str]) -> str:
        """Build the tool-tier block for the router system prompt.

        Each enabled tool contributes one entry with its ``router_tier``
        token, ``description``, and ``examples``.  Disabled tools are
        omitted entirely, removing their tier from the prompt and
        preventing phantom classifications.

        Args:
            enabled_names: Set of currently enabled tool names.

        Returns:
            A formatted multi-line string for insertion into the router
            system prompt, or an empty string if no tools are enabled.
        """
        lines: list[str] = []
        for t in self._tools.values():
            if t.name not in enabled_names:
                continue
            if t.approach != "A":
                continue
            examples_str = ", ".join(f"'{e}'" for e in t.examples)
            lines.append(
                f"  {t.router_tier:<14} — {t.description}\n"
                f"    (e.g. {examples_str})"
            )
        return "\n".join(lines)

    def dispatch(
        self,
        tier: str,
        query: str,
        enabled_names: set[str],
        current_route_tier: str,
        store: MemoryStore | None = None,
    ) -> str | None:
        """Dispatch a query to the matching enabled tool.

        Finds the first tool whose ``router_tier`` matches ``tier``,
        verifies it is enabled and that ``current_route_tier`` meets its
        ``min_tier`` requirement, then calls its ``callable`` with the
        raw query string.

        Enforcement happens here at execution time, not only at the
        UI/schema layer — a tool is refused even if it somehow appears
        in the schema sent to the model.

        If the tool's callable declares a ``store`` keyword parameter, the
        live ``MemoryStore`` (or ``None`` when memory is disabled) is
        injected automatically — tools that do not need it simply omit
        the parameter from their signature.

        Args:
            tier: The classification token produced by the router.
            query: The raw user query string, passed to the tool callable.
            enabled_names: Set of currently enabled tool names.
            current_route_tier: The route tier for this turn; used to
              enforce ``min_tier``.  Tool tiers resolve to rank 0 via the
              rank table default.
            store: Optional live ``MemoryStore`` passed to tools that
              declare a ``store`` parameter.  ``None`` when memory is
              disabled or unavailable.

        Returns:
            The tool callable's return value (a result string or ``None``
            if the tool signals it cannot handle the query), or ``None``
            if no matching enabled tool exists or ``min_tier`` is not met.
        """
        for t in self._tools.values():
            if t.router_tier != tier:
                continue
            if t.name not in enabled_names:
                logging.debug(
                    "Tool %r is disabled; skipping dispatch for tier %r",
                    t.name,
                    tier,
                )
                return None
            current_rank = _TIER_RANK.get(current_route_tier, 0)
            min_rank = _TIER_RANK.get(t.min_tier, 0)
            if current_rank < min_rank:
                logging.debug(
                    "Tool %r requires min_tier %r (rank %d); "
                    "current_route_tier %r (rank %d) insufficient",
                    t.name,
                    t.min_tier,
                    min_rank,
                    current_route_tier,
                    current_rank,
                )
                return None
            sig = inspect.signature(t.callable)
            if "store" in sig.parameters:
                return t.callable(query, store=store)
            return t.callable(query)
        return None

    def schemas(self, enabled_names: set[str]) -> list[dict]:
        """Return OpenAI-compatible schemas for enabled Approach B tools.

        Args:
            enabled_names: Set of currently enabled tool names.

        Returns:
            A list of ``{"type": "function", ...}`` dicts for all enabled
            Approach B tools that have a ``parameters_schema`` defined.
        """
        result = []
        for t in self._tools.values():
            if t.name not in enabled_names:
                continue
            if t.approach != "B" or t.parameters_schema is None:
                continue
            result.append(
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters_schema,
                        "strict": True,
                    },
                }
            )
        return result


#: Global registry singleton.  All tool modules register with this instance.
REGISTRY = ToolRegistry()
