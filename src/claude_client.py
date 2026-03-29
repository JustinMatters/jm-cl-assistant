import os
from typing import Literal

import openai

SONNET_MODEL_ID = "anthropic/claude-sonnet-4-6"
OPUS_MODEL_ID = "anthropic/claude-opus-4-6"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_MODEL_MAP = {
    "sonnet": SONNET_MODEL_ID,
    "opus": OPUS_MODEL_ID,
}


class ClaudeClient:
    def __init__(self) -> None:
        api_key = os.environ["OPENROUTER_API_KEY"]
        self._client = openai.OpenAI(
            base_url=OPENROUTER_BASE_URL,
            api_key=api_key,
        )

    def ask(
        self,
        query: str,
        model: Literal["sonnet", "opus"],
        history: list,
    ) -> str:
        messages = list(history) + [{"role": "user", "content": query}]
        response = self._client.chat.completions.create(
            model=_MODEL_MAP[model],
            messages=messages,
        )
        return response.choices[0].message.content
