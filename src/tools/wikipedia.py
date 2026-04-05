"""Wikipedia summary tool using the Wikipedia REST API (no key required).

Approach B tool — the LLM decides when to call it and supplies the
search topic as a structured argument.  Results are sanitised before
returning to mitigate indirect prompt injection from article content.
"""

from __future__ import annotations

import json
import logging
import unicodedata
import urllib.parse
import urllib.request

from src.tools.registry import REGISTRY, ToolDefinition

_API_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
_HEADERS = {
    "User-Agent": "jm-cl-assistant/1.0 (educational project)",
    "Accept": "application/json",
}

# Maximum characters for the extract before truncation
_MAX_EXTRACT = 600

# OpenAI-compatible parameter schema for Approach B function calling
_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "topic": {
            "type": "string",
            "description": (
                "The topic, person, place, or concept to look up on Wikipedia"
            ),
        }
    },
    "required": ["topic"],
    "additionalProperties": False,
}


def _sanitise(text: str, max_len: int) -> str:
    """Strip control/format characters and truncate.

    Args:
        text: Raw string from Wikipedia.
        max_len: Maximum output length.

    Returns:
        Sanitised, truncated string.
    """
    cleaned = "".join(
        ch
        for ch in text
        if ch == " " or unicodedata.category(ch) not in ("Cc", "Cf")
    )
    cleaned = cleaned.strip()
    if len(cleaned) > max_len:
        # Truncate at a sentence boundary if possible
        truncated = cleaned[:max_len]
        last_dot = truncated.rfind(". ")
        if last_dot > max_len // 2:
            cleaned = truncated[: last_dot + 1]
        else:
            cleaned = truncated.rstrip() + "\u2026"
    return cleaned


def wiki_summary(topic: str) -> str:
    """Fetch a plain-text summary of a Wikipedia article.

    Args:
        topic: The article title or search topic.

    Returns:
        A sanitised plain-text summary with a URL, or an error message.
    """
    title = urllib.parse.quote(topic.strip().replace(" ", "_"))
    url = _API_URL.format(title=title)
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except urllib.request.HTTPError as exc:
        if exc.code == 404:
            return f"No Wikipedia article found for '{topic}'."
        logging.warning("Wikipedia API HTTP error: %s", exc)
        return f"(Wikipedia API error: {exc})"
    except Exception as exc:
        logging.warning("Wikipedia API request failed: %s", exc)
        return f"(Wikipedia API error: {exc})"

    extract = data.get("extract", "")
    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
    title_display = data.get("title", topic)

    if not extract:
        return f"No summary available for '{topic}'."

    summary = _sanitise(extract, _MAX_EXTRACT)
    result = f"{title_display}: {summary}"
    if page_url:
        result += f"\n{page_url}"
    return result


def _wiki_callable(args_json: str) -> str | None:
    """Approach B callable — parses JSON arguments and calls wiki_summary.

    Args:
        args_json: JSON string with a ``topic`` key, as provided by the
          LLM tool-calling loop.

    Returns:
        A plain-text summary string, or ``None`` if arguments cannot be
        parsed or the API returns an error.
    """
    try:
        args = json.loads(args_json)
        topic = args.get("topic", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return None

    if not topic:
        return None

    result = wiki_summary(topic)
    if result.startswith("(Wikipedia API error:"):
        return None
    return result


REGISTRY.register(
    ToolDefinition(
        name="wikipedia",
        router_tier="wikipedia",
        label="Tool: Wikipedia",
        description=(
            "factual summaries about people, places, concepts, events, "
            "or anything with a Wikipedia article"
        ),
        examples=[
            "who is Alan Turing",
            "tell me about the Eiffel Tower",
            "what is quantum entanglement",
            "summary of the French Revolution",
        ],
        default_enabled=True,
        min_tier="simple_ollama",
        approach="B",
        callable=_wiki_callable,
        category="web",
        parameters_schema=_PARAMETERS_SCHEMA,
    )
)
