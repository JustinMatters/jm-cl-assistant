"""OpenRouter API client for Claude Sonnet and Opus models.

Wraps the OpenAI-compatible REST API exposed by OpenRouter, targeting
Anthropic's Claude models.  Requires the OPENROUTER_API_KEY environment
variable to be set.
"""

import base64
import io
import os
from collections.abc import Callable, Iterator
from typing import TYPE_CHECKING, Literal

import openai

from src.model_config import load_models

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

_MODEL_CONFIG = load_models()
SONNET_MODEL_ID = _MODEL_CONFIG["advanced_llm"].model_id
OPUS_MODEL_ID = _MODEL_CONFIG["complex_llm"].model_id
SONNET_DISPLAY_NAME = _MODEL_CONFIG["advanced_llm"].display_name
OPUS_DISPLAY_NAME = _MODEL_CONFIG["complex_llm"].display_name
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_MODEL_MAP = {
    "sonnet": SONNET_MODEL_ID,
    "opus": OPUS_MODEL_ID,
}

# USD per million tokens (OpenRouter pricing, April 2025).
PRICING: dict[str, dict[str, float]] = {
    SONNET_MODEL_ID: {"input": 3.0, "output": 15.0},
    OPUS_MODEL_ID: {"input": 15.0, "output": 75.0},
}


def calculate_cost(
    model_id: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """Calculate the estimated USD cost for a single API call.

    Args:
        model_id: The OpenRouter model identifier.
        prompt_tokens: Number of input (prompt) tokens billed.
        completion_tokens: Number of output (completion) tokens billed.

    Returns:
        Estimated cost in USD, or ``0.0`` if the model is not in the
        ``PRICING`` table.
    """
    pricing = PRICING.get(model_id)
    if pricing is None:
        return 0.0
    return (
        prompt_tokens * pricing["input"] + completion_tokens * pricing["output"]
    ) / 1_000_000


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
        self.last_usage: dict | None = None

    def ask(
        self,
        query: str,
        model: Literal["sonnet", "opus"],
        history: list,
        tools: list[dict] | None = None,
        tool_executor: Callable[[str, str], str] | None = None,
        max_tool_iterations: int = 5,
        image: "PILImage | None" = None,
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
            image: Optional PIL Image to include as a vision content
              block alongside the text query.  Encoded as a base64 PNG
              data URL.  Only sent on the first user turn.

        Returns:
            The assistant's final reply as a plain string.
        """
        if image is not None:
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            user_content = [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
            ]
        else:
            user_content = query
        messages = list(history) + [{"role": "user", "content": user_content}]
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
                if response.usage is not None:
                    self.last_usage = {
                        "prompt_tokens": (response.usage.prompt_tokens or 0),
                        "completion_tokens": (
                            response.usage.completion_tokens or 0
                        ),
                        "total_tokens": (response.usage.total_tokens or 0),
                        "model_id": _MODEL_MAP[model],
                    }
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

    def stream_ask(
        self,
        query: str,
        model: Literal["sonnet", "opus"],
        history: list,
        image: "PILImage | None" = None,
    ) -> Iterator[str]:
        """Stream content chunks from a Claude model via OpenRouter.

        Unlike ``ask()``, this method does not run the Approach B
        tool-use loop.  It is called only when no tool schemas are
        active, so the response is always a plain text stream.

        Args:
            query: The user's message to send.
            model: Which Claude model to use — ``"sonnet"`` or
              ``"opus"``.
            history: Previous conversation turns.
            image: Optional PIL Image included as a base64 PNG vision
              block.

        Yields:
            Content string chunks as they arrive from the streaming API.
        """
        if image is not None:
            buf = io.BytesIO()
            image.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            user_content = [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                },
            ]
        else:
            user_content = query
        messages = list(history) + [{"role": "user", "content": user_content}]
        try:
            stream = self._client.chat.completions.create(
                messages=messages,
                model=_MODEL_MAP[model],
                timeout=60,
                stream=True,
                stream_options={"include_usage": True},
            )
            _last_usage = None
            for chunk in stream:
                if chunk.usage is not None:
                    _last_usage = chunk.usage
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            if _last_usage is not None:
                self.last_usage = {
                    "prompt_tokens": _last_usage.prompt_tokens or 0,
                    "completion_tokens": (_last_usage.completion_tokens or 0),
                    "total_tokens": _last_usage.total_tokens or 0,
                    "model_id": _MODEL_MAP[model],
                }
        except openai.AuthenticationError:
            yield (
                "(OpenRouter authentication failed — "
                "check your OPENROUTER_API_KEY)"
            )
        except openai.RateLimitError:
            yield ("(OpenRouter rate limit hit — please wait and try again)")
        except openai.APIConnectionError:
            yield (
                "(OpenRouter is unreachable — "
                "please check your internet connection)"
            )
        except openai.APIStatusError as exc:
            yield (
                f"(OpenRouter returned HTTP {exc.status_code} — "
                "please try again)"
            )
