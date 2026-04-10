"""Web search tool using the DuckDuckGo Search API.

Performs a text search and returns a concise plain-text summary of the
top results suitable for passing back to an LLM or reading aloud via TTS.

Security: All result text (titles, snippets, URLs) is sanitised before
injection into the LLM context to mitigate indirect prompt-injection
attacks via search results.
"""

from __future__ import annotations

import re as _re
import unicodedata

from ddgs import DDGS

from src.tools.registry import REGISTRY, ToolDefinition

# Maximum characters for each field per result
_MAX_TITLE = 120
_MAX_SNIPPET = 300
_MAX_URL = 200

# Maximum number of results to return
_MAX_RESULTS = 3

# Maximum total output length
_MAX_OUTPUT = 1500

# Preamble patterns to strip before sending to DuckDuckGo
_SEARCH_PREAMBLE = _re.compile(
    r"^\s*(?:"
    r"search(?:\s+(?:for|the\s+web\s+for|online\s+for))?(?:\s+|$)|"
    r"look\s+up\s+|"
    r"find\s+(?:information\s+(?:about|on)\s+)?|"
    r"google\s+|"
    r"web\s+search\s+(?:for\s+)?"
    r")",
    _re.IGNORECASE,
)


def _sanitise(text: str, max_len: int) -> str:
    """Strip control characters and truncate to max_len.

    Removes characters in Unicode categories Cc (control) and Cf
    (format), which are a common indirect prompt-injection vector in
    web content.

    Args:
        text: Raw string to sanitise.
        max_len: Maximum output length in characters.

    Returns:
        Sanitised and truncated string.
    """
    cleaned = "".join(
        ch
        for ch in text
        if ch == " " or unicodedata.category(ch) not in ("Cc", "Cf")
    )
    cleaned = cleaned.strip()
    if len(cleaned) > max_len:
        cleaned = cleaned[:max_len].rstrip() + "\u2026"
    return cleaned


def web_search(query: str, max_results: int = _MAX_RESULTS) -> str:
    """Search DuckDuckGo and return a plain-text summary of top results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to include in the output.

    Returns:
        A plain-text string with title, snippet, and URL for each result,
        or an error message if the search fails or returns no results.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
    except Exception as exc:
        return f"(Web search error: {exc})"

    if not results:
        return "No results found."

    lines: list[str] = []
    for i, r in enumerate(results, 1):
        title = _sanitise(r.get("title") or "", _MAX_TITLE)
        snippet = _sanitise(r.get("body") or "", _MAX_SNIPPET)
        url = _sanitise(r.get("href") or "", _MAX_URL)
        lines.append(f"{i}. {title}\n   {snippet}\n   {url}")

    output = "\n\n".join(lines)
    if len(output) > _MAX_OUTPUT:
        output = output[:_MAX_OUTPUT].rstrip() + "\n\u2026"
    return output


def _handle_web_search_query(query: str) -> str | None:
    """Handle a raw web search query by stripping preamble and searching.

    Strips common natural-language preamble (e.g. "search for …",
    "look up …") before sending the cleaned query to DuckDuckGo.
    Returns ``None`` on error so the orchestrator can fall back to LLM.

    Args:
        query: The raw user query string.

    Returns:
        A plain-text summary of search results, or ``None`` if the query
        is empty after stripping or the search raises an exception.
    """
    cleaned = _SEARCH_PREAMBLE.sub("", query).strip()
    if not cleaned:
        return None
    result = web_search(cleaned)
    if result.startswith("(Web search error:"):
        return None
    return result


REGISTRY.register(
    ToolDefinition(
        name="web_search",
        router_tier="web_search",
        label="Tool: web search",
        description=(
            "queries requiring current information from the internet: "
            "news, recent events, facts, prices, sports results, or "
            "anything the model may not know"
        ),
        examples=[
            "search for latest Python news",
            "what is the current price of gold",
            "look up recent AI developments",
            "who won the last World Cup",
        ],
        default_enabled=True,
        min_tier="trivial_llm",
        approach="A",
        callable=_handle_web_search_query,
        category="web",
    )
)
