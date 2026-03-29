from typing import Literal

import ollama

OLLAMA_MODEL = "sam860/deepseek-r1-0528-qwen3:8b"

_VALID = frozenset({"simple", "complex_sonnet", "complex_opus"})
_FALLBACK: Literal["simple", "complex_sonnet", "complex_opus"] = "simple"

_SYSTEM_PROMPT = (
    "You are a query complexity classifier. "
    "Given a user query, respond with EXACTLY ONE of these words:\n\n"
    "  simple         — factual lookups, basic questions, greetings\n"
    "  complex_sonnet — analysis, essays, multi-step reasoning\n"
    "  complex_opus   — cutting-edge research, expert proofs, "
    "highly complex multi-domain problems\n\n"
    "Output only the single classification word. No punctuation, "
    "no explanation."
)


class OllamaRouter:
    def __init__(self, model: str = OLLAMA_MODEL) -> None:
        self._model = model

    def classify(
        self, query: str
    ) -> Literal["simple", "complex_sonnet", "complex_opus"]:
        response = ollama.chat(
            model=self._model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": query or "(empty query)"},
            ],
        )
        raw = response["message"]["content"].strip().lower()
        if raw in _VALID:
            return raw  # type: ignore[return-value]
        return _FALLBACK
