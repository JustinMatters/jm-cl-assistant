"""Integration tests requiring a live Ollama instance and valid API keys."""

import os

import ollama
import pytest

orchestrator_module = pytest.importorskip("src.orchestrator")
router_module = pytest.importorskip("src.router")
Orchestrator = orchestrator_module.Orchestrator
OLLAMA_FAST_MODEL = router_module.OLLAMA_FAST_MODEL
OLLAMA_MODEL = router_module.OLLAMA_MODEL

_skip_no_api_key = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason=(
        "OPENROUTER_API_KEY is not set — skipping tests that instantiate "
        "Orchestrator (which requires the key at init time)"
    ),
)


@pytest.mark.integration
class TestEnvironment:
    """Pre-flight checks that runtime environment is correctly configured."""

    def test_openrouter_api_key_is_set(self):
        key = os.environ.get("OPENROUTER_API_KEY", "")
        assert key, (
            "OPENROUTER_API_KEY is not set or empty. "
            "Export it before running integration tests."
        )

    def test_fast_model_is_available(self, ollama_server):
        models = [m["model"] for m in ollama.list()["models"]]
        assert any(OLLAMA_FAST_MODEL in m for m in models), (
            f"{OLLAMA_FAST_MODEL} is not pulled. "
            f"Run: ollama run {OLLAMA_FAST_MODEL}"
        )

    def test_ollama_model_is_available(self, ollama_server):
        models = [m["model"] for m in ollama.list()["models"]]
        assert any(OLLAMA_MODEL in m for m in models), (
            f"{OLLAMA_MODEL} is not pulled. Run: ollama run {OLLAMA_MODEL}"
        )


@pytest.mark.integration
@_skip_no_api_key
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


@pytest.mark.integration
@_skip_no_api_key
class TestIntegrationRouting:
    """Verify each routing tier reaches the correct Ollama model."""

    def test_trivial_query_uses_fast_model(self, ollama_server):
        orch = Orchestrator()
        orch.respond("hi", [])
        assert OLLAMA_FAST_MODEL in orch.last_backend

    def test_trivial_query_returns_non_empty_response(self, ollama_server):
        orch = Orchestrator()
        response, _ = orch.respond("what is 2+2", [])
        assert isinstance(response, str)
        assert len(response) > 0

    def test_simple_query_uses_ollama_model(self, ollama_server):
        orch = Orchestrator()
        orch.respond("Tell me about the solar system in one paragraph.", [])
        assert OLLAMA_MODEL.split("/")[-1] in orch.last_backend

    def test_fast_model_responds_directly(self, ollama_server):
        """Fast model answers directly without routing through the 8B model."""
        orch = Orchestrator()
        response, _ = orch.respond("hi", [])
        assert isinstance(response, str)
        assert len(response) > 0
