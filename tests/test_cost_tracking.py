"""Unit tests for Phase 26 — Token and Cost Display (T26.5).

Covers: calculate_cost correctness, Ollama path zero cost, session total
accumulation, last_usage capture, reset_session_cost.
"""

import pytest

openrouter = pytest.importorskip("src.openrouter_client")
calculate_cost = openrouter.calculate_cost
PRICING = openrouter.PRICING
SONNET_MODEL_ID = openrouter.SONNET_MODEL_ID
OPUS_MODEL_ID = openrouter.OPUS_MODEL_ID

orchestrator_module = pytest.importorskip("src.orchestrator")
Orchestrator = orchestrator_module.Orchestrator


# ── calculate_cost ───────────────────────────────────────────────────────────


class TestCalculateCost:
    def test_sonnet_known_tokens(self):
        # 1 000 prompt + 1 000 completion at $3/$15 per million
        cost = calculate_cost(SONNET_MODEL_ID, 1_000, 1_000)
        expected = (1_000 * 3.0 + 1_000 * 15.0) / 1_000_000
        assert abs(cost - expected) < 1e-10

    def test_opus_known_tokens(self):
        cost = calculate_cost(OPUS_MODEL_ID, 2_000, 500)
        expected = (2_000 * 15.0 + 500 * 75.0) / 1_000_000
        assert abs(cost - expected) < 1e-10

    def test_unknown_model_returns_zero(self):
        assert calculate_cost("some/unknown-model", 1000, 1000) == 0.0

    def test_zero_tokens_returns_zero(self):
        assert calculate_cost(SONNET_MODEL_ID, 0, 0) == 0.0

    def test_returns_float(self):
        assert isinstance(calculate_cost(SONNET_MODEL_ID, 100, 100), float)

    def test_sonnet_pricing_in_table(self):
        assert SONNET_MODEL_ID in PRICING

    def test_opus_pricing_in_table(self):
        assert OPUS_MODEL_ID in PRICING

    def test_pricing_has_input_output_keys(self):
        for model_id, prices in PRICING.items():
            assert "input" in prices, model_id
            assert "output" in prices, model_id


# ── Orchestrator usage attributes ────────────────────────────────────────────


class TestOrchestratorUsageDefaults:
    def test_last_usage_initially_none(self, mocker):
        mocker.patch("src.orchestrator.OpenRouterClient")
        mocker.patch("src.orchestrator.OllamaRouter")
        mocker.patch("src.orchestrator.MemoryStore")
        orch = Orchestrator(memory_enabled=False)
        assert orch.last_usage is None

    def test_last_cost_initially_zero(self, mocker):
        mocker.patch("src.orchestrator.OpenRouterClient")
        mocker.patch("src.orchestrator.OllamaRouter")
        mocker.patch("src.orchestrator.MemoryStore")
        orch = Orchestrator(memory_enabled=False)
        assert orch.last_cost == 0.0

    def test_session_cost_initially_zero(self, mocker):
        mocker.patch("src.orchestrator.OpenRouterClient")
        mocker.patch("src.orchestrator.OllamaRouter")
        mocker.patch("src.orchestrator.MemoryStore")
        orch = Orchestrator(memory_enabled=False)
        assert orch.session_cost == 0.0


class TestResetSessionCost:
    def test_resets_session_cost(self, mocker):
        mocker.patch("src.orchestrator.OpenRouterClient")
        mocker.patch("src.orchestrator.OllamaRouter")
        orch = Orchestrator(memory_enabled=False)
        orch.session_cost = 1.23
        orch.reset_session_cost()
        assert orch.session_cost == 0.0

    def test_resets_last_cost(self, mocker):
        mocker.patch("src.orchestrator.OpenRouterClient")
        mocker.patch("src.orchestrator.OllamaRouter")
        orch = Orchestrator(memory_enabled=False)
        orch.last_cost = 0.5
        orch.reset_session_cost()
        assert orch.last_cost == 0.0

    def test_resets_last_usage(self, mocker):
        mocker.patch("src.orchestrator.OpenRouterClient")
        mocker.patch("src.orchestrator.OllamaRouter")
        orch = Orchestrator(memory_enabled=False)
        orch.last_usage = {"prompt_tokens": 10}
        orch.reset_session_cost()
        assert orch.last_usage is None


# ── Ollama path produces zero cost ───────────────────────────────────────────


class TestOllamaZeroCost:
    def test_ollama_respond_sets_last_usage(self, mocker):
        mocker.patch("src.orchestrator.OpenRouterClient")
        mocker.patch("src.orchestrator.OllamaRouter")
        fake_result = {
            "message": {"content": "hi", "tool_calls": None},
            "prompt_eval_count": 10,
            "eval_count": 5,
            "done": True,
        }
        mocker.patch("ollama.chat", return_value=fake_result)
        orch = Orchestrator(memory_enabled=False)
        orch._ollama_respond("hi", [], "qwen3:1.7b")
        assert orch.last_usage is not None
        assert orch.last_usage["prompt_tokens"] == 10
        assert orch.last_usage["completion_tokens"] == 5

    def test_ollama_respond_no_cost_accumulation(self, mocker):
        mocker.patch("src.orchestrator.OpenRouterClient")
        mocker.patch("src.orchestrator.OllamaRouter")
        fake_result = {
            "message": {"content": "hi", "tool_calls": None},
            "prompt_eval_count": 100,
            "eval_count": 50,
            "done": True,
        }
        mocker.patch("ollama.chat", return_value=fake_result)
        orch = Orchestrator(memory_enabled=False)
        orch._ollama_respond("hi", [], "qwen3:1.7b")
        # session_cost unchanged — Ollama has no pricing
        assert orch.session_cost == 0.0
        assert orch.last_cost == 0.0


# ── Session cost accumulates across Claude calls ─────────────────────────────


class TestSessionCostAccumulation:
    def _make_orch(self, mocker):
        mocker.patch("src.orchestrator.OllamaRouter")
        claude_mock = mocker.patch(
            "src.orchestrator.OpenRouterClient"
        ).return_value
        orch = Orchestrator(memory_enabled=False)
        return orch, claude_mock

    def test_session_cost_accumulates(self, mocker):
        orch, claude_mock = self._make_orch(mocker)
        # Router returns advanced_llm twice
        orch._router.classify = mocker.Mock(return_value="advanced_llm")
        claude_mock.ask.return_value = "response"
        usage = {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "model_id": SONNET_MODEL_ID,
        }
        claude_mock.last_usage = usage
        mocker.patch("src.tools.registry.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.tools.registry.REGISTRY.schemas", return_value=[])

        orch.respond("hello", [])
        cost1 = orch.session_cost
        orch.respond("world", [])
        cost2 = orch.session_cost

        expected_per_call = calculate_cost(SONNET_MODEL_ID, 100, 50)
        assert abs(cost1 - expected_per_call) < 1e-10
        assert abs(cost2 - 2 * expected_per_call) < 1e-10

    def test_last_cost_set_per_call(self, mocker):
        orch, claude_mock = self._make_orch(mocker)
        orch._router.classify = mocker.Mock(return_value="advanced_llm")
        claude_mock.ask.return_value = "response"
        claude_mock.last_usage = {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "model_id": SONNET_MODEL_ID,
        }
        mocker.patch("src.tools.registry.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.tools.registry.REGISTRY.schemas", return_value=[])

        orch.respond("test", [])
        expected = calculate_cost(SONNET_MODEL_ID, 200, 100)
        assert abs(orch.last_cost - expected) < 1e-10
