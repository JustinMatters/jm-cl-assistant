import pytest

app_module = pytest.importorskip("src.app")
_check_ollama_models = app_module._check_ollama_models
_check_api_key = app_module._check_api_key


def _make_model(name: str, mocker):
    m = mocker.MagicMock()
    m.model = name
    return m


class TestCheckOllamaModels:
    def test_returns_none_when_all_models_present(self, mocker):
        mock_list = mocker.MagicMock()
        mock_list.models = [
            _make_model("qwen3:1.7b", mocker),
            _make_model("sam860/deepseek-r1-0528-qwen3:8b", mocker),
        ]
        mocker.patch("src.app.ollama.list", return_value=mock_list)
        MODEL = "sam860/deepseek-r1-0528-qwen3:8b"
        assert _check_ollama_models("qwen3:1.7b", MODEL) is None

    def test_returns_warning_when_model_missing(self, mocker):
        mock_list = mocker.MagicMock()
        mock_list.models = [_make_model("qwen3:1.7b", mocker)]
        mocker.patch("src.app.ollama.list", return_value=mock_list)
        result = _check_ollama_models(
            "qwen3:1.7b", "sam860/deepseek-r1-0528-qwen3:8b"
        )
        assert result is not None
        assert "sam860/deepseek-r1-0528-qwen3:8b" in result

    def test_warning_includes_pull_command(self, mocker):
        mock_list = mocker.MagicMock()
        mock_list.models = []
        mocker.patch("src.app.ollama.list", return_value=mock_list)
        result = _check_ollama_models("qwen3:1.7b")
        assert "ollama pull qwen3:1.7b" in result

    def test_returns_none_when_ollama_unreachable(self, mocker):
        mocker.patch(
            "src.app.ollama.list",
            side_effect=ConnectionError("Ollama not running"),
        )
        assert _check_ollama_models("qwen3:1.7b") is None

    def test_accepts_model_with_latest_tag_variant(self, mocker):
        mock_list = mocker.MagicMock()
        mock_list.models = [_make_model("qwen3:latest", mocker)]
        mocker.patch("src.app.ollama.list", return_value=mock_list)
        # "qwen3:1.7b" shares base "qwen3" but different tag — should be missing
        result = _check_ollama_models("qwen3:1.7b")
        assert result is not None

    def test_no_models_requested_returns_none(self, mocker):
        mock_list = mocker.MagicMock()
        mock_list.models = []
        mocker.patch("src.app.ollama.list", return_value=mock_list)
        assert _check_ollama_models() is None


class TestCheckApiKey:
    def test_returns_none_when_key_is_set(self, mocker):
        mocker.patch.dict("os.environ", {"OPENROUTER_API_KEY": "sk-test"})
        assert _check_api_key() is None

    def test_returns_warning_when_key_missing(self, mocker):
        mocker.patch.dict("os.environ", {}, clear=True)
        result = _check_api_key()
        assert result is not None
        assert "OPENROUTER_API_KEY" in result

    def test_warning_mentions_claude_unavailable(self, mocker):
        mocker.patch.dict("os.environ", {}, clear=True)
        result = _check_api_key()
        assert "unavailable" in result.lower()
