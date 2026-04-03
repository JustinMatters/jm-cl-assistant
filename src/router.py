"""Query complexity classifier backed by a local Ollama model.

Routes each user query to one of four tiers — trivial_ollama,
simple_ollama, complex_sonnet, or complex_opus — by prompting a local
LLM to classify the query's difficulty.
"""

import warnings
from typing import Literal

import ollama

OLLAMA_MODEL = "sam860/deepseek-r1-0528-qwen3:8b"
OLLAMA_FAST_MODEL = "qwen3:1.7b"

_VALID = frozenset(
    {
        "trivial_ollama",
        "simple_ollama",
        "complex_sonnet",
        "complex_opus",
        "maths",
    }
)
_FALLBACK: Literal[
    "trivial_ollama",
    "simple_ollama",
    "complex_sonnet",
    "complex_opus",
    "maths",
] = "trivial_ollama"

_SYSTEM_PROMPT = (
    "You are a query complexity classifier. "
    "Given a user query, respond with EXACTLY ONE of these tokens:\n\n"
    "  trivial_ollama — greetings, and any question with a short definitive "
    "answer that a schoolchild would know: capital cities, country facts, "
    "basic geography, historical dates, famous people, yes/no facts, "
    "translations, colours, simple definitions "
    "(e.g. 'hi', 'what colour is the sky', 'what is the capital of France', "
    "'who wrote Romeo and Juliet', 'how do you say hello in Spanish')\n"
    "  maths          — arithmetic, algebra, and any query whose answer is a "
    "number: expressions to evaluate, percentages, powers, roots, "
    "trigonometry, unit conversions involving numbers "
    "(e.g. 'what is 2+2', 'calculate sqrt(144)', '15% of 200', "
    "'2**10', 'convert 5 miles to km')\n"
    "  simple_ollama  — questions requiring a paragraph or more to answer: "
    "how-to instructions, explanations of concepts, short summaries, "
    "defining acronyms or terms "
    "(e.g. 'how does photosynthesis work', "
    "'explain what a REST API is', 'what does API stand for')\n"
    "  complex_sonnet — analysis, essays, multi-step reasoning, "
    "comparisons, structured writing; NOT short summaries or definitions\n"
    "  complex_opus   — cutting-edge research, expert proofs, "
    "highly complex multi-domain problems; "
    "NOT short summaries or definitions\n\n"
    "Output only the single classification token. No punctuation, "
    "no explanation."
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
        self, query: str
    ) -> Literal[
        "trivial_ollama",
        "simple_ollama",
        "complex_sonnet",
        "complex_opus",
        "maths",
    ]:
        """Classify a user query by complexity.

        Prompts the local Ollama model with the query and parses the
        single-token classification response.  Falls back to
        ``"trivial_ollama"`` if the model returns an unrecognised value.

        Args:
            query: The user's input text.  An empty string is sent as
              ``"(empty query)"`` to avoid API errors.

        Returns:
            One of ``"trivial_ollama"``, ``"simple_ollama"``,
            ``"complex_sonnet"``, ``"complex_opus"``, or ``"maths"``.
        """
        try:
            response = ollama.chat(
                model=self._model,
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
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
        if raw in _VALID:
            return raw  # type: ignore[return-value]
        return _FALLBACK
