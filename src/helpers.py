"""Utility helpers shared across the jm-cl-assistant source modules."""

import re


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
