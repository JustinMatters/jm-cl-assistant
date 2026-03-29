"""Integration tests requiring a live Ollama instance and valid API keys."""

import os

import pytest

orchestrator_module = pytest.importorskip("src.orchestrator")
Orchestrator = orchestrator_module.Orchestrator


@pytest.mark.integration
class TestEnvironment:
    """Pre-flight checks that runtime environment is correctly configured."""

    def test_openrouter_api_key_is_set(self):
        key = os.environ.get("OPENROUTER_API_KEY", "")
        assert key, (
            "OPENROUTER_API_KEY is not set or empty. "
            "Export it before running integration tests."
        )


@pytest.mark.integration
class TestIntegrationOrchestrator:
    def test_simple_query_returns_non_empty_response(self, ollama_server):
        orch = Orchestrator()
        response, history = orch.respond("What is the capital of France?", [])
        assert isinstance(response, str)
        assert len(response) > 0

    def test_history_grows_after_each_turn(self, ollama_server):
        orch = Orchestrator()
        _, history = orch.respond("Hello", [])
        assert len(history) >= 2

    def test_multi_turn_conversation(self, ollama_server):
        orch = Orchestrator()
        _, history = orch.respond("My name is Alice.", [])
        response, history = orch.respond("What is my name?", history)
        assert isinstance(response, str)
        assert len(response) > 0

    def test_respond_does_not_raise_on_long_input(self, ollama_server):
        orch = Orchestrator()
        long_query = "Explain this concept. " * 50
        response, _ = orch.respond(long_query, [])
        assert isinstance(response, str)
