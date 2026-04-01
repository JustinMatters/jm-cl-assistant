import openai
import pytest

openrouter_module = pytest.importorskip("src.openrouter_client")
OpenRouterClient = openrouter_module.OpenRouterClient

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
