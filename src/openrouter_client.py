"""OpenRouter API client for Claude Sonnet and Opus models.

Wraps the OpenAI-compatible REST API exposed by OpenRouter, targeting
Anthropic's Claude models.  Requires the OPENROUTER_API_KEY environment
variable to be set.
"""

import os
from typing import Literal

import openai

SONNET_MODEL_ID = "anthropic/claude-sonnet-4-6"
OPUS_MODEL_ID = "anthropic/claude-opus-4-6"
SONNET_DISPLAY_NAME = "Claude Sonnet"
OPUS_DISPLAY_NAME = "Claude Opus"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_MODEL_MAP = {
    "sonnet": SONNET_MODEL_ID,
    "opus": OPUS_MODEL_ID,
}


class OpenRouterClient:
    """Client for querying Claude models via the OpenRouter API.

    Reads OPENROUTER_API_KEY from the environment on construction and
    raises KeyError if it is absent.
    """

    def __init__(self) -> None:
        try:
            api_key = os.environ["OPENROUTER_API_KEY"]
        except KeyError:
            raise ValueError(
                "Set the OPENROUTER_API_KEY environment variable "
                "before running the app"
            ) from None
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
        """Send a query to a Claude model and return the response text.

        Args:
            query: The user's message to send.
            model: Which Claude model to use — ``"sonnet"`` maps to
              claude-sonnet-4-6 and ``"opus"`` to claude-opus-4-6.
            history: Previous conversation turns as a list of
              ``{"role": ..., "content": ...}`` dicts.

        Returns:
            The assistant's reply as a plain string.
        """
        messages = list(history) + [{"role": "user", "content": query}]
        try:
            response = self._client.chat.completions.create(
                model=_MODEL_MAP[model],
                messages=messages,
                timeout=60,
            )
            return response.choices[0].message.content
        except openai.AuthenticationError:
            return (
                "(OpenRouter authentication failed — "
                "check your OPENROUTER_API_KEY)"
            )
        except openai.RateLimitError:
            return "(OpenRouter rate limit hit — please wait and try again)"
        except openai.APIConnectionError:
            return (
                "(OpenRouter is unreachable — "
                "please check your internet connection)"
            )
        except openai.APIStatusError as exc:
            return (
                f"(OpenRouter returned HTTP {exc.status_code} — "
                "please try again)"
            )
