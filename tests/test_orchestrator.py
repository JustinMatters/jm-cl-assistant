import pytest

orchestrator_module = pytest.importorskip("src.orchestrator")
Orchestrator = orchestrator_module.Orchestrator


class TestOrchestratorRespond:
    def _make_orchestrator(self, mocker, classification):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value=classification,
        )
        return Orchestrator(session_id="test-session", memory_enabled=False)

    def test_trivial_query_answered_by_fast_ollama(self, mocker):
        orch = self._make_orchestrator(mocker, "trivial_ollama")
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="Hello!",
        )
        response, _ = orch.respond("hi", [])
        mock_ollama.assert_called_once()
        _, _, model_arg = mock_ollama.call_args.args
        assert model_arg == orch._fast_model
        assert response == "Hello!"

    def test_simple_query_answered_by_slow_ollama(self, mocker):
        orch = self._make_orchestrator(mocker, "simple_ollama")
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="Paris",
        )
        response, _ = orch.respond("What is the capital of France?", [])
        mock_ollama.assert_called_once()
        _, _, model_arg = mock_ollama.call_args.args
        assert model_arg == orch._ollama_model
        assert response == "Paris"

    def test_complex_sonnet_query_answered_by_claude_sonnet(self, mocker):
        orch = self._make_orchestrator(mocker, "complex_sonnet")
        mock_claude = mocker.patch(
            "src.orchestrator.OpenRouterClient.ask",
            return_value="A detailed answer.",
        )
        response, _ = orch.respond("Explain the French Revolution.", [])
        mock_claude.assert_called_once_with(mocker.ANY, "sonnet", mocker.ANY)
        assert response == "A detailed answer."

    def test_complex_opus_query_answered_by_claude_opus(self, mocker):
        orch = self._make_orchestrator(mocker, "complex_opus")
        mock_claude = mocker.patch(
            "src.orchestrator.OpenRouterClient.ask",
            return_value="A highly detailed answer.",
        )
        response, _ = orch.respond("Prove the Riemann hypothesis.", [])
        mock_claude.assert_called_once_with(mocker.ANY, "opus", mocker.ANY)
        assert response == "A highly detailed answer."

    def test_history_is_returned_updated(self, mocker):
        orch = self._make_orchestrator(mocker, "trivial_ollama")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="Paris",
        )
        _, history = orch.respond("What is the capital of France?", [])
        assert len(history) > 0

    def test_existing_history_is_preserved(self, mocker):
        orch = self._make_orchestrator(mocker, "simple_ollama")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="Berlin",
        )
        prior_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        _, history = orch.respond("What is the capital?", prior_history)
        assert len(history) > len(prior_history)

    def test_respond_returns_tuple_of_str_and_list(self, mocker):
        orch = self._make_orchestrator(mocker, "trivial_ollama")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="answer",
        )
        result = orch.respond("A question?", [])
        assert isinstance(result, tuple)
        assert isinstance(result[0], str)
        assert isinstance(result[1], list)

    def test_ollama_not_called_for_complex_sonnet(self, mocker):
        orch = self._make_orchestrator(mocker, "complex_sonnet")
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond"
        )
        mocker.patch(
            "src.orchestrator.OpenRouterClient.ask",
            return_value="answer",
        )
        orch.respond("A complex question.", [])
        mock_ollama.assert_not_called()

    def test_ollama_not_called_for_complex_opus(self, mocker):
        orch = self._make_orchestrator(mocker, "complex_opus")
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond"
        )
        mocker.patch(
            "src.orchestrator.OpenRouterClient.ask",
            return_value="answer",
        )
        orch.respond("A very hard question.", [])
        mock_ollama.assert_not_called()

    def test_claude_not_called_for_trivial_query(self, mocker):
        orch = self._make_orchestrator(mocker, "trivial_ollama")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="answer",
        )
        mock_claude = mocker.patch("src.orchestrator.OpenRouterClient.ask")
        orch.respond("hi", [])
        mock_claude.assert_not_called()

    def test_claude_not_called_for_simple_query(self, mocker):
        orch = self._make_orchestrator(mocker, "simple_ollama")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="answer",
        )
        mock_claude = mocker.patch("src.orchestrator.OpenRouterClient.ask")
        orch.respond("A simple question.", [])
        mock_claude.assert_not_called()


class TestOrchestratorOllamaErrorHandling:
    def test_connection_error_returns_friendly_string(self, mocker):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value="trivial_ollama",
        )
        mocker.patch(
            "src.orchestrator.ollama.chat",
            side_effect=ConnectionError("Ollama not running"),
        )
        orch = Orchestrator(memory_enabled=False)
        response, _ = orch.respond("hi", [])
        assert "Ollama error" in response

    def test_response_error_returns_friendly_string(self, mocker):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value="simple_ollama",
        )
        mocker.patch(
            "src.orchestrator.ollama.chat",
            side_effect=Exception("model not found"),
        )
        orch = Orchestrator(memory_enabled=False)
        response, _ = orch.respond("A question", [])
        assert "Ollama error" in response

    def test_ollama_error_still_updates_history(self, mocker):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value="trivial_ollama",
        )
        mocker.patch(
            "src.orchestrator.ollama.chat",
            side_effect=ConnectionError("Ollama not running"),
        )
        orch = Orchestrator(memory_enabled=False)
        _, history = orch.respond("hi", [])
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"
