"""Utility helpers shared across the jm-cl-assistant source modules."""

import io
import logging
import re
import wave

import numpy as np


def strip_think_tags(text: str) -> str:
    """Remove all <think>…</think> blocks from a string and strip whitespace.

    Some LLMs (e.g. DeepSeek R1) wrap chain-of-thought reasoning in
    ``<think>`` tags before the final answer.  This function removes those
    blocks so only the answer text is displayed.

    Args:
        text: The raw LLM response, which may contain zero or more
          ``<think>…</think>`` blocks.

    Returns:
        The input string with all ``<think>`` blocks removed and leading /
        trailing whitespace stripped.
    """
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def strip_markdown(text: str) -> str:
    """Remove common Markdown formatting symbols from a string.

    Preserves the readable content but removes syntax characters such as
    asterisks, underscores, hashes, and backticks so that TTS engines do
    not vocalise them (e.g. "asterisk asterisk bold asterisk asterisk").

    The following constructs are handled:

    - Fenced code blocks (``` … ```)
    - Inline code (`` ` … ` ``)
    - Links ``[text](url)`` → ``text``
    - Bold/italic: ``***``, ``**``, ``*``, ``___``, ``__``, ``_``
    - ATX headings (``# … ######``)
    - Blockquotes (``> ``)
    - Horizontal rules (``---``, ``***``, ``___``)

    Args:
        text: A string that may contain Markdown formatting.

    Returns:
        The input string with Markdown symbols removed.
    """
    # Fenced code blocks
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    # Inline code
    text = re.sub(r"`[^`]+`", "", text)
    # Links: [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Bold + italic ***text*** / ___text___
    text = re.sub(r"\*{3}(.+?)\*{3}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_{3}(.+?)_{3}", r"\1", text, flags=re.DOTALL)
    # Bold **text** / __text__
    text = re.sub(r"\*{2}(.+?)\*{2}", r"\1", text, flags=re.DOTALL)
    text = re.sub(r"_{2}(.+?)_{2}", r"\1", text, flags=re.DOTALL)
    # Italic *text* / _text_
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"_(.+?)_", r"\1", text)
    # ATX headings
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Blockquotes
    text = re.sub(r"^>\s?", "", text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
    # Unordered list markers (- item, * item, + item)
    text = re.sub(r"^[-*+]\s+", "", text, flags=re.MULTILINE)
    # Ordered list markers (1. item, 12. item)
    text = re.sub(r"^\d+\.\s+", "", text, flags=re.MULTILINE)
    return text.strip()


def to_wav_bytes(arr: np.ndarray, sample_rate: int) -> bytes:
    """Convert a float32 audio array to WAV bytes.

    Clips values to ``[-1, 1]``, scales to int16, and encodes as a
    mono WAV in memory. Returning ``bytes`` to ``gr.Audio`` bypasses
    Gradio's internal float32-to-int16 conversion and its associated
    warning.

    Args:
        arr: Float32 audio samples, shape ``(N,)`` or ``(N, channels)``.
        sample_rate: Sample rate in Hz.

    Returns:
        WAV-encoded audio as a ``bytes`` object.
    """
    arr_int16 = (np.clip(arr.flatten(), -1.0, 1.0) * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(arr_int16.tobytes())
    return buf.getvalue()


def count_tokens(messages: list[dict]) -> int:
    """Estimate the token count of a list of message dicts.

    Uses a characters-divided-by-four heuristic that avoids any external
    tokeniser dependency.  Accurate enough for budget checking; actual
    token counts vary by model and content.

    Text content in vision messages (list-form content blocks) is summed
    over text-type parts only — image data is excluded.

    Args:
        messages: List of ``{"role": ..., "content": ...}`` dicts.

    Returns:
        Estimated total token count across all messages.
    """
    total = 0
    for msg in messages:
        content = msg.get("content") or ""
        if isinstance(content, str):
            total += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    total += len(part.get("text", ""))
    return total // 4


def trim_history(augmented: list, budget: int) -> tuple[list, bool]:
    """Trim history to fit within a token budget.

    Drops the oldest non-system user+assistant message pairs until
    ``count_tokens(augmented) <= budget``.  System messages are always
    preserved.  If ``budget`` is ``0`` or negative, returns the input
    unchanged (no-limit mode).

    Args:
        augmented: Conversation history, possibly prefixed with injected
          system messages.
        budget: Maximum estimated token count.  ``0`` disables trimming.

    Returns:
        ``(trimmed_history, was_trimmed)`` — ``was_trimmed`` is ``True``
        when at least one pair was dropped.
    """
    if budget <= 0 or count_tokens(augmented) <= budget:
        return augmented, False

    system_msgs = [m for m in augmented if m.get("role") == "system"]
    non_system = [m for m in augmented if m.get("role") != "system"]

    while (
        len(non_system) >= 2 and count_tokens(system_msgs + non_system) > budget
    ):
        non_system = non_system[2:]

    return system_msgs + non_system, True


def suppress_connection_reset_errors() -> None:
    """Suppress the Windows asyncio ConnectionResetError log noise.

    On Windows, closing a browser tab while Gradio has an open websocket
    causes Python's asyncio proactor to log a ``ConnectionResetError``
    traceback.  This function installs a logging filter on the ``asyncio``
    logger that silences those records while leaving all other asyncio
    errors visible.
    """

    class _ConnectionResetFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return not (
                record.exc_info and record.exc_info[0] is ConnectionResetError
            )

    logging.getLogger("asyncio").addFilter(_ConnectionResetFilter())
