"""Dictionary / definition tool using the Free Dictionary API.

Uses api.dictionaryapi.dev with the ``en_GB`` locale for UK English
spellings and definitions.  No API key required.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.request

from src.tools.registry import REGISTRY, ToolDefinition

_API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en_GB/{word}"
_HEADERS = {"User-Agent": "jm-cl-assistant/1.0"}

# Maximum definitions per part-of-speech entry
_MAX_DEFS = 3

# Preamble patterns to strip before looking up the word
_DEFINE_PREAMBLE = re.compile(
    r"^\s*(?:define\s+|definition\s+of\s+|what\s+(?:does\s+|is\s+(?:the\s+"
    r"(?:meaning|definition)\s+of\s+)?)?|meaning\s+of\s+|look\s+up\s+)",
    re.IGNORECASE,
)


def define(word: str) -> str:
    """Look up a word in the UK English dictionary.

    Returns the phonetic transcription, up to three parts of speech,
    and up to three definitions each, plus an example sentence where
    available.

    Args:
        word: The word to look up.

    Returns:
        A plain-text definition string, or an error/not-found message.
    """
    word = word.strip().lower()
    if not word:
        return "Please provide a word to look up."

    url = _API_URL.format(word=urllib.request.quote(word))
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except urllib.request.HTTPError as exc:
        if exc.code == 404:
            return f"No definition found for '{word}'."
        logging.warning("Dictionary API HTTP error: %s", exc)
        return f"(Dictionary API error: {exc})"
    except Exception as exc:
        logging.warning("Dictionary API request failed: %s", exc)
        return f"(Dictionary API error: {exc})"

    if not data:
        return f"No definition found for '{word}'."

    entry = data[0]
    headword = entry.get("word", word)
    phonetic = entry.get("phonetic", "")

    phonetic_str = f"  /{phonetic}/" if phonetic else ""
    lines: list[str] = [f"**{headword}**{phonetic_str}"]

    for meaning in entry.get("meanings", [])[:_MAX_DEFS]:
        pos = meaning.get("partOfSpeech", "")
        lines.append(f"\n_{pos}_")
        for i, defn in enumerate(meaning.get("definitions", [])[:_MAX_DEFS], 1):
            text = defn.get("definition", "")
            example = defn.get("example", "")
            lines.append(f"  {i}. {text}")
            if example:
                lines.append(f'     e.g. "{example}"')

    return "\n".join(lines)


def _handle_define_query(query: str) -> str | None:
    """Handle a raw define/lookup query by extracting the word.

    Args:
        query: The raw user query, e.g. ``"define ephemeral"`` or
          ``"what does sanguine mean"``.

    Returns:
        A plain-text definition string, or ``None`` if no word could
        be extracted.
    """
    word = _DEFINE_PREAMBLE.sub("", query).strip().rstrip("?.")
    # Take only the first word/phrase (up to 3 words) after stripping
    parts = word.split()
    if not parts:
        return None
    word = " ".join(parts[:3])
    result = define(word)
    if result.startswith("(Dictionary API error:"):
        return None
    return result


REGISTRY.register(
    ToolDefinition(
        name="dictionary",
        router_tier="dictionary",
        label="Tool: dictionary",
        description=(
            "definitions, meanings, and word lookups — "
            "what a word means, its part of speech, or how it is used"
        ),
        examples=[
            "define ephemeral",
            "what does sanguine mean",
            "definition of ubiquitous",
            "meaning of perfidious",
        ],
        default_enabled=True,
        min_tier="trivial_ollama",
        approach="A",
        callable=_handle_define_query,
        category="general",
    )
)
