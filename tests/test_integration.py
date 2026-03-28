import pytest

orchestrator_module = pytest.importorskip("src.orchestrator")
Orchestrator = orchestrator_module.Orchestrator


@pytest.mark.integration
class TestIntegrationOrchestrator:
    def test_simple_query_returns_non_empty_response(self):
        orch = Orchestrator()
        response, history = orch.respond("What is the capital of France?", [])
        assert isinstance(response, str)
        assert len(response) > 0

    def test_history_grows_after_each_turn(self):
        orch = Orchestrator()
        _, history = orch.respond("Hello", [])
        assert len(history) >= 2

    def test_multi_turn_conversation(self):
        orch = Orchestrator()
        _, history = orch.respond("My name is Alice.", [])
        response, history = orch.respond("What is my name?", history)
        assert isinstance(response, str)
        assert len(response) > 0

    def test_respond_does_not_raise_on_long_input(self):
        orch = Orchestrator()
        long_query = "Explain this concept. " * 50
        response, _ = orch.respond(long_query, [])
        assert isinstance(response, str)
