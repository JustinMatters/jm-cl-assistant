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
