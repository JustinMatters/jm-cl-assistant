from unittest.mock import MagicMock

import pytest

orchestrator_module = pytest.importorskip("src.orchestrator")
Orchestrator = orchestrator_module.Orchestrator

from src.tools.registry import REGISTRY  # noqa: E402

_MEMORY_BLOCK = (
    "[PAST MEMORIES]\n- [2026-01-01 | conversation] A fact.\n[END MEMORIES]"
)


class TestOrchestratorRespond:
    def _make_orchestrator(self, mocker, classification):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value=classification,
        )
        return Orchestrator(session_id="test-session", memory_enabled=False)

    def test_trivial_query_answered_by_fast_ollama(self, mocker):
        orch = self._make_orchestrator(mocker, "trivial_llm")
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
        orch = self._make_orchestrator(mocker, "simple_llm")
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="Paris",
        )
        response, _ = orch.respond("What is the capital of France?", [])
        mock_ollama.assert_called_once()
        _, _, model_arg = mock_ollama.call_args.args
        assert model_arg == orch._ollama_model
        assert response == "Paris"

    def test_advanced_llm_query_answered_by_claude_sonnet(self, mocker):
        orch = self._make_orchestrator(mocker, "advanced_llm")
        mock_claude = mocker.patch(
            "src.orchestrator.OpenRouterClient.ask",
            return_value="A detailed answer.",
        )
        response, _ = orch.respond("Explain the French Revolution.", [])
        mock_claude.assert_called_once_with(
            mocker.ANY,
            "sonnet",
            mocker.ANY,
            tools=mocker.ANY,
            tool_executor=mocker.ANY,
            image=None,
        )
        assert response == "A detailed answer."

    def test_complex_llm_query_answered_by_claude_opus(self, mocker):
        orch = self._make_orchestrator(mocker, "complex_llm")
        mock_claude = mocker.patch(
            "src.orchestrator.OpenRouterClient.ask",
            return_value="A highly detailed answer.",
        )
        response, _ = orch.respond("Prove the Riemann hypothesis.", [])
        mock_claude.assert_called_once_with(
            mocker.ANY,
            "opus",
            mocker.ANY,
            tools=mocker.ANY,
            tool_executor=mocker.ANY,
            image=None,
        )
        assert response == "A highly detailed answer."

    def test_history_is_returned_updated(self, mocker):
        orch = self._make_orchestrator(mocker, "trivial_llm")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="Paris",
        )
        _, history = orch.respond("What is the capital of France?", [])
        assert len(history) > 0

    def test_existing_history_is_preserved(self, mocker):
        orch = self._make_orchestrator(mocker, "simple_llm")
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
        orch = self._make_orchestrator(mocker, "trivial_llm")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="answer",
        )
        result = orch.respond("A question?", [])
        assert isinstance(result, tuple)
        assert isinstance(result[0], str)
        assert isinstance(result[1], list)

    def test_ollama_not_called_for_advanced_llm(self, mocker):
        orch = self._make_orchestrator(mocker, "advanced_llm")
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond"
        )
        mocker.patch(
            "src.orchestrator.OpenRouterClient.ask",
            return_value="answer",
        )
        orch.respond("A complex question.", [])
        mock_ollama.assert_not_called()

    def test_ollama_not_called_for_complex_llm(self, mocker):
        orch = self._make_orchestrator(mocker, "complex_llm")
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
        orch = self._make_orchestrator(mocker, "trivial_llm")
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="answer",
        )
        mock_claude = mocker.patch("src.orchestrator.OpenRouterClient.ask")
        orch.respond("hi", [])
        mock_claude.assert_not_called()

    def test_claude_not_called_for_simple_query(self, mocker):
        orch = self._make_orchestrator(mocker, "simple_llm")
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
            return_value="trivial_llm",
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
            return_value="simple_llm",
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
            return_value="trivial_llm",
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


class TestContextInjection:
    """Memory context is injected as a system message when relevant."""

    def _make_orch_with_memory(self, mocker, context_block):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value="trivial_llm",
        )
        orch = Orchestrator(session_id="test-session", memory_enabled=False)
        mock_memory = MagicMock()
        mock_memory.get_context_block.return_value = context_block
        orch._memory = mock_memory
        return orch

    def test_system_message_injected_when_memories_exist(self, mocker):
        orch = self._make_orch_with_memory(mocker, _MEMORY_BLOCK)
        mock_respond = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="reply",
        )
        orch.respond("hello", [])
        passed_history = mock_respond.call_args.args[1]
        assert passed_history[0]["role"] == "system"
        assert "[PAST MEMORIES]" in passed_history[0]["content"]

    def test_no_system_message_when_store_empty(self, mocker):
        orch = self._make_orch_with_memory(mocker, "")
        mock_respond = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="reply",
        )
        orch.respond("hello", [])
        passed_history = mock_respond.call_args.args[1]
        assert all(m["role"] != "system" for m in passed_history)

    def test_no_system_message_when_query_is_whitespace(self, mocker):
        orch = self._make_orch_with_memory(mocker, _MEMORY_BLOCK)
        mock_respond = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="reply",
        )
        orch.respond("   ", [])
        passed_history = mock_respond.call_args.args[1]
        assert all(m["role"] != "system" for m in passed_history)

    def test_injected_context_not_added_to_returned_history(self, mocker):
        orch = self._make_orch_with_memory(mocker, _MEMORY_BLOCK)
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="reply",
        )
        _, updated = orch.respond("hello", [])
        assert all(m["role"] != "system" for m in updated)


class TestMemoryEnabledPerCall:
    """memory_enabled=False at call time suppresses reads and writes."""

    def _make_orch(self, mocker):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value="trivial_llm",
        )
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="reply",
        )
        orch = Orchestrator(session_id="test-session", memory_enabled=False)
        mock_memory = MagicMock()
        mock_memory.get_context_block.return_value = _MEMORY_BLOCK
        orch._memory = mock_memory
        return orch

    def test_disabled_skips_context_read(self, mocker):
        orch = self._make_orch(mocker)
        orch.respond("hello", [], memory_enabled=False)
        orch._memory.get_context_block.assert_not_called()

    def test_disabled_skips_memory_write(self, mocker):
        orch = self._make_orch(mocker)
        orch.respond("hello", [], memory_enabled=False)
        orch._memory.add.assert_not_called()

    def test_enabled_reads_and_writes(self, mocker):
        orch = self._make_orch(mocker)
        orch.respond("hello", [], memory_enabled=True)
        orch._memory.get_context_block.assert_called_once()
        orch._memory.add.assert_called_once()


class TestMathsDispatch:
    """maths classification calls the calculator tool via the registry."""

    def _make_orch(self, mocker):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value="maths",
        )
        return Orchestrator(session_id="test-session", memory_enabled=False)

    def test_maths_query_answered_by_tool(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(REGISTRY, "dispatch", return_value="4")
        response, _ = orch.respond("what is 2 + 2?", [])
        assert response == "4"

    def test_ollama_not_called_when_tool_succeeds(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(REGISTRY, "dispatch", return_value="4")
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond"
        )
        orch.respond("what is 2 + 2?", [])
        mock_ollama.assert_not_called()

    def test_claude_not_called_when_tool_succeeds(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(REGISTRY, "dispatch", return_value="4")
        mock_claude = mocker.patch("src.orchestrator.OpenRouterClient.ask")
        orch.respond("what is 2 + 2?", [])
        mock_claude.assert_not_called()

    def test_backend_label_is_tool_calculator(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(REGISTRY, "dispatch", return_value="4")
        orch.respond("what is 2 + 2?", [])
        assert orch.last_backend == "Tool: calculator"

    def test_tool_failure_falls_back_to_fast_ollama(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(REGISTRY, "dispatch", return_value=None)
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="fallback answer",
        )
        response, _ = orch.respond("what day is it?", [])
        mock_ollama.assert_called_once()
        _, _, model_arg = mock_ollama.call_args.args
        assert model_arg == orch._fast_model
        assert response == "fallback answer"

    def test_tool_failure_updates_backend_away_from_tool(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(REGISTRY, "dispatch", return_value=None)
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="fallback",
        )
        orch.respond("what day is it?", [])
        assert orch.last_backend != "Tool: calculator"

    def test_dispatch_called_with_classification_and_query(self, mocker):
        orch = self._make_orch(mocker)
        mock_dispatch = mocker.patch.object(
            REGISTRY, "dispatch", return_value="42"
        )
        orch.respond("calculate 6 * 7", [])
        call_args = mock_dispatch.call_args
        assert call_args.args[0] == "maths"
        assert call_args.args[1] == "calculate 6 * 7"


class TestConvertDispatch:
    """convert classification calls the converter tool via the registry."""

    def _make_orch(self, mocker):
        mocker.patch(
            "src.orchestrator.OllamaRouter.classify",
            return_value="convert",
        )
        return Orchestrator(session_id="test-session", memory_enabled=False)

    _CONV_RESULT = "5 mi = 8.047 km"

    def test_convert_query_answered_by_tool(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(
            REGISTRY, "dispatch", return_value=self._CONV_RESULT
        )
        response, _ = orch.respond("convert 5 miles to km", [])
        assert response == self._CONV_RESULT

    def test_ollama_not_called_when_tool_succeeds(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(
            REGISTRY, "dispatch", return_value=self._CONV_RESULT
        )
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond"
        )
        orch.respond("convert 5 miles to km", [])
        mock_ollama.assert_not_called()

    def test_claude_not_called_when_tool_succeeds(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(
            REGISTRY, "dispatch", return_value=self._CONV_RESULT
        )
        mock_claude = mocker.patch("src.orchestrator.OpenRouterClient.ask")
        orch.respond("convert 5 miles to km", [])
        mock_claude.assert_not_called()

    def test_backend_label_is_tool_converter(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(
            REGISTRY, "dispatch", return_value=self._CONV_RESULT
        )
        orch.respond("convert 5 miles to km", [])
        assert orch.last_backend == "Tool: converter"

    def test_tool_failure_falls_back_to_fast_ollama(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(REGISTRY, "dispatch", return_value=None)
        mock_ollama = mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="fallback answer",
        )
        response, _ = orch.respond("convert things", [])
        mock_ollama.assert_called_once()
        assert response == "fallback answer"

    def test_tool_failure_updates_backend_away_from_tool(self, mocker):
        orch = self._make_orch(mocker)
        mocker.patch.object(REGISTRY, "dispatch", return_value=None)
        mocker.patch(
            "src.orchestrator.Orchestrator._ollama_respond",
            return_value="fallback",
        )
        orch.respond("convert 5 kg to meters", [])
        assert orch.last_backend != "Tool: converter"

    def test_dispatch_called_with_classification_and_query(self, mocker):
        orch = self._make_orch(mocker)
        mock_dispatch = mocker.patch.object(
            REGISTRY, "dispatch", return_value="5 mi = 8.047 km"
        )
        orch.respond("convert 5 miles to km", [])
        call_args = mock_dispatch.call_args
        assert call_args.args[0] == "convert"
        assert call_args.args[1] == "convert 5 miles to km"
