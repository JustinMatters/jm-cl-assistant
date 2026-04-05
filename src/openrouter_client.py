"""OpenRouter API client for Claude Sonnet and Opus models.

Wraps the OpenAI-compatible REST API exposed by OpenRouter, targeting
Anthropic's Claude models.  Requires the OPENROUTER_API_KEY environment
variable to be set.
"""

import os
from collections.abc import Callable
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
        tools: list[dict] | None = None,
        tool_executor: Callable[[str, str], str] | None = None,
        max_tool_iterations: int = 5,
    ) -> str:
        """Send a query to a Claude model and return the response text.

        When ``tools`` and ``tool_executor`` are provided, runs an
        agentic loop: if the model returns ``finish_reason="tool_calls"``,
        executes each requested tool via ``tool_executor``, appends the
        results, and resends until the model returns a text response or
        ``max_tool_iterations`` tool rounds have elapsed.

        Args:
            query: The user's message to send.
            model: Which Claude model to use — ``"sonnet"`` maps to
              claude-sonnet-4-6 and ``"opus"`` to claude-opus-4-6.
            history: Previous conversation turns as a list of
              ``{"role": ..., "content": ...}`` dicts.
            tools: OpenAI-compatible tool schemas (from
              ``ToolRegistry.schemas()``).  Passed verbatim in the
              ``tools`` field of the API request.  ``None`` or ``[]``
              disables tool calling entirely.
            tool_executor: Callable invoked as
              ``tool_executor(name, arguments_json)`` where
              ``arguments_json`` is the raw JSON string the model
              produced.  Must return a result string.  Required when
              ``tools`` is non-empty; ignored otherwise.
            max_tool_iterations: Maximum number of tool-call rounds
              before the loop is terminated with a guard message.

        Returns:
            The assistant's final reply as a plain string.
        """
        messages = list(history) + [{"role": "user", "content": query}]
        create_kwargs: dict = {
            "model": _MODEL_MAP[model],
            "timeout": 60,
        }
        if tools:
            create_kwargs["tools"] = tools

        tool_rounds = 0
        while True:
            try:
                response = self._client.chat.completions.create(
                    messages=messages, **create_kwargs
                )
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

            choice = response.choices[0]
            if (
                choice.finish_reason != "tool_calls"
                or not tools
                or not tool_executor
            ):
                return choice.message.content or ""

            # Append assistant message preserving tool call metadata.
            msg = choice.message
            messages.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )
            for tc in msg.tool_calls:
                result = tool_executor(tc.function.name, tc.function.arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result,
                    }
                )

            tool_rounds += 1
            if tool_rounds >= max_tool_iterations:
                return (
                    f"(Tool loop reached {max_tool_iterations} iterations"
                    " without a final response)"
                )
