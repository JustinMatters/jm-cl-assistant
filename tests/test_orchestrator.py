import pytest

orchestrator_module = pytest.importorskip("src.orchestrator")
Orchestrator = orchestrator_module.Orchestrator


class TestOrchestratorRespond:
    def _make_orchestrator(self, mocker, classification):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value=classification,
        )
        return Orchestrator()

    def test_simple_query_answered_by_ollama(self, mocker):
        orch = self._make_orchestrator(mocker, "simple")
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="Paris",
        )
        response, _ = orch.respond("What is the capital of France?", [])
        mock_ollama.assert_called_once()
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
        orch = self._make_orchestrator(mocker, "simple")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="Paris",
        )
        _, history = orch.respond("What is the capital of France?", [])
        assert len(history) > 0

    def test_existing_history_is_preserved(self, mocker):
        orch = self._make_orchestrator(mocker, "simple")
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
        orch = self._make_orchestrator(mocker, "simple")
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

    def test_claude_not_called_for_simple_query(self, mocker):
        orch = self._make_orchestrator(mocker, "simple")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="answer",
        )
        mock_claude = mocker.patch("src.orchestrator.OpenRouterClient.ask")
        orch.respond("A simple question.", [])
        mock_claude.assert_not_called()
