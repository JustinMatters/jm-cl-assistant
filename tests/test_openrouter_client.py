import json

import openai
import pytest

openrouter_module = pytest.importorskip("src.openrouter_client")
OpenRouterClient = openrouter_module.OpenRouterClient


def _tool_response(mocker, name, args_dict, call_id="call_1"):
    """Build a mock API response with a single tool_call."""
    tc = mocker.MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = json.dumps(args_dict)

    msg = mocker.MagicMock()
    msg.content = None
    msg.tool_calls = [tc]

    choice = mocker.MagicMock()
    choice.finish_reason = "tool_calls"
    choice.message = msg

    resp = mocker.MagicMock()
    resp.choices = [choice]
    return resp


def _text_response(mocker, content):
    """Build a mock API response with a plain text reply."""
    msg = mocker.MagicMock()
    msg.content = content

    choice = mocker.MagicMock()
    choice.finish_reason = "stop"
    choice.message = msg

    resp = mocker.MagicMock()
    resp.choices = [choice]
    return resp


SONNET_MODEL_ID = "anthropic/claude-sonnet-4-6"
OPUS_MODEL_ID = "anthropic/claude-opus-4-6"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class TestOpenRouterClientAsk:
    def test_ask_returns_string(self, mocker):
        mock_create = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_create.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = "An answer."
        client = OpenRouterClient()
        result = client.ask("A question?", "sonnet", [])
        assert isinstance(result, str)

    def test_sonnet_uses_correct_model_id(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = OpenRouterClient()
        client.ask("A question?", "sonnet", [])
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == SONNET_MODEL_ID

    def test_opus_uses_correct_model_id(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = OpenRouterClient()
        client.ask("A question?", "opus", [])
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == OPUS_MODEL_ID

    def test_uses_openrouter_base_url(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_openai.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = "answer"
        OpenRouterClient()
        _, kwargs = mock_openai.call_args
        assert kwargs.get("base_url") == OPENROUTER_BASE_URL

    def test_messages_include_user_query(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = OpenRouterClient()
        client.ask("Tell me about Paris.", "sonnet", [])
        _, kwargs = mock_create.call_args
        messages = kwargs["messages"]
        user_messages = [m for m in messages if m["role"] == "user"]
        assert any("Paris" in m["content"] for m in user_messages)

    def test_history_is_included_in_messages(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = OpenRouterClient()
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        client.ask("Follow-up question.", "sonnet", history)
        _, kwargs = mock_create.call_args
        messages = kwargs["messages"]
        assert len(messages) > len(history)

    def test_api_key_read_from_environment(self, mocker):
        mocker.patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key-123"})
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_openai.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = "answer"
        OpenRouterClient()
        _, kwargs = mock_openai.call_args
        assert kwargs.get("api_key") == "test-key-123"

    def test_missing_api_key_raises_value_error(self, mocker):
        mocker.patch.dict("os.environ", {}, clear=True)
        mocker.patch("src.openrouter_client.openai.OpenAI")
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
            OpenRouterClient()

    def test_timeout_passed_to_create(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = OpenRouterClient()
        client.ask("A question?", "sonnet", [])
        _, kwargs = mock_create.call_args
        assert "timeout" in kwargs


class TestOpenRouterClientErrorHandling:
    def _make_client(self, mocker):
        mocker.patch("src.openrouter_client.openai.OpenAI")
        return OpenRouterClient()

    def _mock_create(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        return mock_openai.return_value.chat.completions.create

    def test_authentication_error_returns_friendly_string(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.side_effect = openai.AuthenticationError(
            "Unauthorized", response=mocker.MagicMock(), body=None
        )
        client = OpenRouterClient()
        result = client.ask("question", "sonnet", [])
        assert "authentication failed" in result.lower()

    def test_rate_limit_error_returns_friendly_string(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.side_effect = openai.RateLimitError(
            "Too Many Requests", response=mocker.MagicMock(), body=None
        )
        client = OpenRouterClient()
        result = client.ask("question", "sonnet", [])
        assert "rate limit" in result.lower()

    def test_connection_error_returns_friendly_string(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.side_effect = openai.APIConnectionError(
            request=mocker.MagicMock()
        )
        client = OpenRouterClient()
        result = client.ask("question", "sonnet", [])
        assert "unreachable" in result.lower()

    def test_api_status_error_includes_status_code(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_response = mocker.MagicMock()
        mock_response.status_code = 503
        mock_create.side_effect = openai.APIStatusError(
            "Service Unavailable", response=mock_response, body=None
        )
        client = OpenRouterClient()
        result = client.ask("question", "sonnet", [])
        assert "503" in result


class TestToolUseLoop:
    """Tests for the Approach B agentic tool-use loop in ask()."""

    def _make_client(self, mocker):
        mocker.patch("src.openrouter_client.openai.OpenAI")
        return OpenRouterClient()

    def _mock_create(self, mocker):
        mock_openai = mocker.patch("src.openrouter_client.openai.OpenAI")
        return mock_openai.return_value.chat.completions.create

    def test_no_tools_kwarg_behaves_as_before(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.return_value.choices[0].message.content = "answer"
        client = OpenRouterClient()
        result = client.ask("q", "sonnet", [])
        assert result == "answer"

    def test_tools_schema_passed_to_api(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.return_value = _text_response(mocker, "done")
        schemas = [{"type": "function", "function": {"name": "calc"}}]
        client = OpenRouterClient()
        client.ask(
            "q", "sonnet", [], tools=schemas, tool_executor=lambda n, a: ""
        )
        _, kwargs = mock_create.call_args
        assert kwargs.get("tools") == schemas

    def test_single_tool_call_round_trip(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.side_effect = [
            _tool_response(mocker, "calc", {"expr": "2+2"}),
            _text_response(mocker, "The answer is 4"),
        ]
        executor = mocker.MagicMock(return_value="4")
        client = OpenRouterClient()
        schemas = [{"type": "function", "function": {"name": "calc"}}]
        result = client.ask(
            "what is 2+2", "sonnet", [], tools=schemas, tool_executor=executor
        )
        assert result == "The answer is 4"
        executor.assert_called_once_with("calc", json.dumps({"expr": "2+2"}))

    def test_executor_called_with_correct_name_and_args(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.side_effect = [
            _tool_response(mocker, "weather", {"city": "London"}, "id_1"),
            _text_response(mocker, "It is sunny"),
        ]
        executor = mocker.MagicMock(return_value="sunny")
        client = OpenRouterClient()
        schemas = [{"type": "function", "function": {"name": "weather"}}]
        client.ask(
            "weather?", "sonnet", [], tools=schemas, tool_executor=executor
        )
        name_arg, args_arg = executor.call_args.args
        assert name_arg == "weather"
        assert json.loads(args_arg) == {"city": "London"}

    def test_tool_result_appended_as_tool_message(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.side_effect = [
            _tool_response(mocker, "calc", {}),
            _text_response(mocker, "done"),
        ]
        client = OpenRouterClient()
        schemas = [{"type": "function", "function": {"name": "calc"}}]
        client.ask(
            "q",
            "sonnet",
            [],
            tools=schemas,
            tool_executor=lambda n, a: "result_42",
        )
        second_call_messages = mock_create.call_args_list[1].kwargs["messages"]
        tool_msgs = [m for m in second_call_messages if m["role"] == "tool"]
        assert len(tool_msgs) == 1
        assert tool_msgs[0]["content"] == "result_42"

    def test_multi_step_chain(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.side_effect = [
            _tool_response(mocker, "step1", {}, "id_a"),
            _tool_response(mocker, "step2", {}, "id_b"),
            _text_response(mocker, "final"),
        ]
        executor = mocker.MagicMock(return_value="ok")
        client = OpenRouterClient()
        schemas = [{"type": "function", "function": {"name": "step1"}}]
        result = client.ask(
            "q", "sonnet", [], tools=schemas, tool_executor=executor
        )
        assert result == "final"
        assert executor.call_count == 2

    def test_max_iterations_guard(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.return_value = _tool_response(mocker, "loop", {})
        executor = mocker.MagicMock(return_value="x")
        client = OpenRouterClient()
        schemas = [{"type": "function", "function": {"name": "loop"}}]
        result = client.ask(
            "q",
            "sonnet",
            [],
            tools=schemas,
            tool_executor=executor,
            max_tool_iterations=3,
        )
        assert "3" in result
        assert executor.call_count == 3

    def test_tool_error_string_propagated_to_model(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.side_effect = [
            _tool_response(mocker, "bad_tool", {}),
            _text_response(mocker, "sorry, tool failed"),
        ]
        client = OpenRouterClient()
        schemas = [{"type": "function", "function": {"name": "bad_tool"}}]
        result = client.ask(
            "q",
            "sonnet",
            [],
            tools=schemas,
            tool_executor=lambda n, a: "Error: tool exploded",
        )
        second_messages = mock_create.call_args_list[1].kwargs["messages"]
        tool_msgs = [m for m in second_messages if m["role"] == "tool"]
        assert "Error" in tool_msgs[0]["content"]
        assert result == "sorry, tool failed"

    def test_empty_tools_list_does_not_pass_tools_to_api(self, mocker):
        mock_create = self._mock_create(mocker)
        mock_create.return_value = _text_response(mocker, "done")
        client = OpenRouterClient()
        client.ask("q", "sonnet", [], tools=[], tool_executor=lambda n, a: "")
        _, kwargs = mock_create.call_args
        assert "tools" not in kwargs


class TestStreamAskErrors:
    """Test stream_ask error handler branches."""

    def _make_client(self, mocker):
        mocker.patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"})
        mocker.patch("openai.OpenAI")
        return OpenRouterClient()

    def test_auth_error_yields_message(self, mocker):
        client = self._make_client(mocker)
        client._client.chat.completions.create.side_effect = (
            openai.AuthenticationError(
                "auth", response=mocker.MagicMock(), body={}
            )
        )
        chunks = list(client.stream_ask("hi", "sonnet", []))
        assert len(chunks) == 1
        assert "authentication failed" in chunks[0]

    def test_rate_limit_error_yields_message(self, mocker):
        client = self._make_client(mocker)
        client._client.chat.completions.create.side_effect = (
            openai.RateLimitError("rate", response=mocker.MagicMock(), body={})
        )
        chunks = list(client.stream_ask("hi", "sonnet", []))
        assert any("rate limit" in c for c in chunks)

    def test_connection_error_yields_message(self, mocker):
        client = self._make_client(mocker)
        client._client.chat.completions.create.side_effect = (
            openai.APIConnectionError(request=mocker.MagicMock())
        )
        chunks = list(client.stream_ask("hi", "sonnet", []))
        assert any("unreachable" in c for c in chunks)

    def test_api_status_error_yields_message(self, mocker):
        client = self._make_client(mocker)
        mock_response = mocker.MagicMock()
        mock_response.status_code = 500
        client._client.chat.completions.create.side_effect = (
            openai.APIStatusError("err", response=mock_response, body={})
        )
        chunks = list(client.stream_ask("hi", "sonnet", []))
        assert any("500" in c for c in chunks)
