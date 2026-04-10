"""Query complexity classifier backed by a local Ollama model.

Routes each user query to one of four tiers — trivial_ollama,
simple_ollama, complex_sonnet, or complex_opus — by prompting a local
LLM to classify the query's difficulty.  When tools are enabled their
router tiers are appended to the valid set and system prompt dynamically;
disabling a tool removes its tier from the prompt entirely, saving tokens
and preventing phantom classifications.
"""

import warnings

import ollama

from src.tools.registry import REGISTRY

OLLAMA_MODEL = "gemma4:e4b"
OLLAMA_FAST_MODEL = "qwen3:1.7b"

_BASE_VALID = frozenset(
    {
        "trivial_ollama",
        "simple_ollama",
        "complex_sonnet",
        "complex_opus",
    }
)
_FALLBACK = "trivial_ollama"

_PROMPT_HEADER = (
    "You are a query complexity classifier. "
    "Given a user query, respond with EXACTLY ONE of these tokens:\n\n"
    "  trivial_ollama — greetings, and any question with a short definitive "
    "answer that a schoolchild would know: capital cities, country facts, "
    "basic geography, historical dates, famous people, yes/no facts, "
    "translations, colours, simple definitions "
    "(e.g. 'hi', 'what colour is the sky', "
    "'what is the capital of France', "
    "'who wrote Romeo and Juliet', 'how do you say hello in Spanish')\n"
)

_PROMPT_LLM_TIERS = (
    "  simple_ollama  — questions requiring a paragraph or more to answer: "
    "how-to instructions, explanations of concepts, short summaries, "
    "defining acronyms or terms "
    "(e.g. 'how does photosynthesis work', "
    "'explain what a REST API is', 'what does API stand for')\n"
    "  complex_sonnet — analysis, essays, multi-step reasoning, "
    "comparisons, structured writing; NOT short summaries or definitions\n"
    "  complex_opus   — cutting-edge research, expert proofs, "
    "highly complex multi-domain problems; "
    "NOT short summaries or definitions\n"
)

_PROMPT_SUFFIX = (
    "\nOutput only the single classification token. "
    "No punctuation, no explanation."
)


class OllamaRouter:
    """Routes queries by complexity using a local Ollama classification model.

    Args:
        model: The Ollama model name used for classification.
          Defaults to OLLAMA_MODEL.

    Attributes:
        _model: The Ollama model name used for classification.
    """

    def __init__(self, model: str = OLLAMA_MODEL) -> None:
        self._model = model

    def classify(
        self,
        query: str,
        enabled_tools: set[str] | None = None,
    ) -> str:
        """Classify a user query by complexity.

        Prompts the local Ollama model with the query and parses the
        single-token classification response.  Falls back to
        ``"trivial_ollama"`` if the model returns an unrecognised value.

        The system prompt and valid-token set are built dynamically from
        ``enabled_tools``.  Base LLM tiers (``trivial_ollama``,
        ``simple_ollama``, ``complex_sonnet``, ``complex_opus``) are
        always present.  Each enabled tool's ``router_tier`` is appended
        in registration order; disabling a tool removes its tier from
        the prompt entirely.

        Args:
            query: The user's input text.  An empty string is sent as
              ``"(empty query)"`` to avoid API errors.
            enabled_tools: Set of tool names currently active.  Tool
              tiers for names in this set are added to the valid set and
              system prompt.  Pass ``None`` or an empty set to omit all
              tool tiers.

        Returns:
            A classification token — one of the four base LLM tiers or
            a registered tool's ``router_tier`` if that tool is enabled.
            Falls back to ``"trivial_ollama"`` on error or unrecognised
            output.
        """
        active = enabled_tools or set()
        tool_tiers = {t.router_tier for t in REGISTRY.enabled_tools(active)}
        valid = _BASE_VALID | tool_tiers

        tool_section = REGISTRY.router_prompt_section(active)
        if tool_section:
            system_prompt = (
                _PROMPT_HEADER
                + tool_section
                + "\n"
                + _PROMPT_LLM_TIERS
                + _PROMPT_SUFFIX
            )
        else:
            system_prompt = _PROMPT_HEADER + _PROMPT_LLM_TIERS + _PROMPT_SUFFIX

        try:
            response = ollama.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query or "(empty query)"},
                ],
            )
            raw = response["message"]["content"].strip().lower()
        except Exception as exc:
            warnings.warn(
                f"Ollama router failed ({exc!r}); "
                f"falling back to {_FALLBACK!r}",
                stacklevel=2,
            )
            return _FALLBACK
        if raw in valid:
            return raw  # type: ignore[return-value]
        return _FALLBACK
