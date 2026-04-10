"""URL content summariser tool using trafilatura for text extraction.

Approach B tool — the LLM decides when to call it, fetches and extracts
the readable content from a URL, and returns it framed as data for the
model to summarise.

Security: extracted content is sanitised and truncated before being
injected into the LLM context to mitigate indirect prompt injection.
The returned text is explicitly framed as source material, not as
instructions, to reduce the risk of injected directives being acted on.
"""

from __future__ import annotations

import json
import logging
import unicodedata
import urllib.parse

import trafilatura

from src.tools.registry import REGISTRY, ToolDefinition

# Maximum characters of extracted text passed back to the LLM
_MAX_CONTENT = 3000

# Allowed URL schemes
_ALLOWED_SCHEMES = {"http", "https"}

# OpenAI-compatible parameter schema for Approach B function calling
_PARAMETERS_SCHEMA = {
    "type": "object",
    "properties": {
        "url": {
            "type": "string",
            "description": "The full URL of the web page to read and summarise",
        }
    },
    "required": ["url"],
    "additionalProperties": False,
}


def _validate_url(url: str) -> str | None:
    """Validate that a URL uses an allowed scheme.

    Args:
        url: The URL string to validate.

    Returns:
        The normalised URL string, or ``None`` if invalid.
    """
    try:
        parsed = urllib.parse.urlparse(url.strip())
    except Exception:
        return None
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        return None
    if not parsed.netloc:
        return None
    return url.strip()


def _sanitise(text: str, max_len: int) -> str:
    """Strip control/format characters and truncate.

    Args:
        text: Raw extracted text.
        max_len: Maximum output length in characters.

    Returns:
        Sanitised, truncated string.
    """
    cleaned = "".join(
        ch
        for ch in text
        if ch in (" ", "\n") or unicodedata.category(ch) not in ("Cc", "Cf")
    )
    cleaned = cleaned.strip()
    if len(cleaned) > max_len:
        truncated = cleaned[:max_len]
        last_para = truncated.rfind("\n\n")
        if last_para > max_len // 2:
            cleaned = truncated[:last_para].rstrip()
        else:
            cleaned = truncated.rstrip() + "\u2026"
    return cleaned


def summarise_url(url: str) -> str:
    """Fetch and extract readable text from a URL.

    Uses trafilatura to extract the main article body, then sanitises
    and truncates the result.  The output is framed as source material
    for the LLM to summarise, reducing indirect prompt injection risk.

    Args:
        url: The URL to fetch.

    Returns:
        A plain-text string containing the extracted content framed for
        summarisation, or an error message.
    """
    validated = _validate_url(url)
    if validated is None:
        return f"Invalid or unsupported URL: {url!r}"

    try:
        downloaded = trafilatura.fetch_url(validated)
    except Exception as exc:
        logging.warning("URL fetch failed for %r: %s", validated, exc)
        return f"(URL fetch error: {exc})"

    if not downloaded:
        return f"Could not fetch content from {validated!r}"

    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
    )

    if not text:
        return f"No readable text could be extracted from {validated!r}"

    content = _sanitise(text, _MAX_CONTENT)
    return (
        f"Content extracted from {validated}:\n\n"
        f"{content}\n\n"
        f"(Source: {validated})"
    )


def _url_reader_callable(args_json: str) -> str | None:
    """Approach B callable — parses JSON arguments and calls summarise_url.

    Args:
        args_json: JSON string with a ``url`` key, as provided by the
          LLM tool-calling loop.

    Returns:
        Extracted content string, or ``None`` if arguments are invalid
        or the fetch fails with an error.
    """
    try:
        args = json.loads(args_json)
        url = args.get("url", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return None

    if not url:
        return None

    result = summarise_url(url)
    if result.startswith("(URL fetch error:"):
        return None
    return result


REGISTRY.register(
    ToolDefinition(
        name="url_reader",
        router_tier="url_reader",
        label="Tool: URL reader",
        description=(
            "fetch and summarise the content of a web page from a URL"
        ),
        examples=[
            "summarise https://example.com/article",
            "what does this page say: https://bbc.co.uk/news/...",
            "read this link for me",
        ],
        default_enabled=True,
        min_tier="complex_sonnet",
        approach="B",
        callable=_url_reader_callable,
        category="web",
        parameters_schema=_PARAMETERS_SCHEMA,
    )
)
