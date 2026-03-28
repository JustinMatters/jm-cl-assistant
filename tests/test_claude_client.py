import pytest

claude_module = pytest.importorskip("src.claude_client")
ClaudeClient = claude_module.ClaudeClient

SONNET_MODEL_ID = "anthropic/claude-sonnet-4-6"
OPUS_MODEL_ID = "anthropic/claude-opus-4-6"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


class TestClaudeClientAsk:
    def test_ask_returns_string(self, mocker):
        mock_create = mocker.patch("src.claude_client.openai.OpenAI")
        mock_create.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = "An answer."
        client = ClaudeClient()
        result = client.ask("A question?", "sonnet", [])
        assert isinstance(result, str)

    def test_sonnet_uses_correct_model_id(self, mocker):
        mock_openai = mocker.patch("src.claude_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = ClaudeClient()
        client.ask("A question?", "sonnet", [])
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == SONNET_MODEL_ID

    def test_opus_uses_correct_model_id(self, mocker):
        mock_openai = mocker.patch("src.claude_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = ClaudeClient()
        client.ask("A question?", "opus", [])
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == OPUS_MODEL_ID

    def test_uses_openrouter_base_url(self, mocker):
        mock_openai = mocker.patch("src.claude_client.openai.OpenAI")
        mock_openai.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = "answer"
        ClaudeClient()
        _, kwargs = mock_openai.call_args
        assert kwargs.get("base_url") == OPENROUTER_BASE_URL

    def test_messages_include_user_query(self, mocker):
        mock_openai = mocker.patch("src.claude_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = ClaudeClient()
        client.ask("Tell me about Paris.", "sonnet", [])
        _, kwargs = mock_create.call_args
        messages = kwargs["messages"]
        user_messages = [m for m in messages if m["role"] == "user"]
        assert any("Paris" in m["content"] for m in user_messages)

    def test_history_is_included_in_messages(self, mocker):
        mock_openai = mocker.patch("src.claude_client.openai.OpenAI")
        mock_create = mock_openai.return_value.chat.completions.create
        mock_create.return_value.choices[0].message.content = "answer"
        client = ClaudeClient()
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
        mock_openai = mocker.patch("src.claude_client.openai.OpenAI")
        mock_openai.return_value.chat.completions.create.return_value.choices[
            0
        ].message.content = "answer"
        ClaudeClient()
        _, kwargs = mock_openai.call_args
        assert kwargs.get("api_key") == "test-key-123"

    def test_missing_api_key_raises(self, mocker):
        mocker.patch.dict("os.environ", {}, clear=True)
        mocker.patch("src.claude_client.openai.OpenAI")
        with pytest.raises((KeyError, ValueError, RuntimeError)):
            ClaudeClient()
