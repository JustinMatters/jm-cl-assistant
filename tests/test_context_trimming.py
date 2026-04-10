"""Unit tests for Phase 24 — Context Window Trimming.

Covers: count_tokens heuristic, trim_history algorithm, orchestrator
integration (budget respected, trim note present, system messages preserved,
no trimming when within budget).
"""

import pytest

helpers_module = pytest.importorskip("src.helpers")
count_tokens = helpers_module.count_tokens
trim_history = helpers_module.trim_history

orchestrator_module = pytest.importorskip("src.orchestrator")
Orchestrator = orchestrator_module.Orchestrator


# ── count_tokens ──────────────────────────────────────────────────────────────


class TestCountTokens:
    def test_empty_list_returns_zero(self):
        assert count_tokens([]) == 0

    def test_single_message_four_chars_one_token(self):
        msgs = [{"role": "user", "content": "test"}]
        assert count_tokens(msgs) == 1

    def test_character_div_four_heuristic(self):
        msgs = [{"role": "user", "content": "a" * 400}]
        assert count_tokens(msgs) == 100

    def test_multiple_messages_summed(self):
        msgs = [
            {"role": "user", "content": "a" * 200},
            {"role": "assistant", "content": "b" * 200},
        ]
        assert count_tokens(msgs) == 100

    def test_none_content_treated_as_empty(self):
        msgs = [{"role": "user", "content": None}]
        assert count_tokens(msgs) == 0

    def test_missing_content_key_treated_as_empty(self):
        msgs = [{"role": "user"}]
        assert count_tokens(msgs) == 0

    def test_vision_content_list_sums_text_parts(self):
        msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "a" * 400},
                    {"type": "image_url", "image_url": {"url": "data:..."}},
                ],
            }
        ]
        assert count_tokens(msgs) == 100

    def test_vision_content_ignores_non_text_parts(self):
        msgs = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": "data:..."}},
                ],
            }
        ]
        assert count_tokens(msgs) == 0


# ── trim_history ──────────────────────────────────────────────────────────────


def _msgs(n_pairs: int, chars_per_msg: int = 4) -> list[dict]:
    """Build n_pairs user+assistant message pairs."""
    msgs = []
    for _i in range(n_pairs):
        msgs.append({"role": "user", "content": "u" * chars_per_msg})
        msgs.append({"role": "assistant", "content": "a" * chars_per_msg})
    return msgs


class TestTrimHistory:
    def test_within_budget_unchanged(self):
        msgs = _msgs(2, chars_per_msg=4)  # ~2 tokens total
        result, trimmed = trim_history(msgs, budget=100)
        assert result == msgs
        assert trimmed is False

    def test_zero_budget_disables_trimming(self):
        msgs = _msgs(100, chars_per_msg=100)  # very long
        result, trimmed = trim_history(msgs, budget=0)
        assert result == msgs
        assert trimmed is False

    def test_negative_budget_disables_trimming(self):
        msgs = _msgs(100, chars_per_msg=100)
        result, trimmed = trim_history(msgs, budget=-1)
        assert result == msgs
        assert trimmed is False

    def test_oversized_history_trimmed(self):
        # 10 pairs × 2 messages × 40 chars = 800 chars → ~200 tokens
        msgs = _msgs(10, chars_per_msg=40)
        result, trimmed = trim_history(msgs, budget=20)
        assert trimmed is True
        assert count_tokens(result) <= 20

    def test_trim_drops_oldest_pairs_first(self):
        msgs = [
            {"role": "user", "content": "oldest user"},
            {"role": "assistant", "content": "oldest asst"},
            {"role": "user", "content": "recent user"},
            {"role": "assistant", "content": "recent asst"},
        ]
        # Budget just enough for one pair (~6 tokens for 2×24 chars)
        result, trimmed = trim_history(msgs, budget=6)
        assert trimmed is True
        contents = [m["content"] for m in result]
        assert "oldest user" not in contents
        assert "recent user" in contents or "recent asst" in contents

    def test_system_messages_preserved(self):
        system = {"role": "system", "content": "You are helpful."}
        user_msgs = _msgs(5, chars_per_msg=40)
        msgs = [system] + user_msgs
        result, trimmed = trim_history(msgs, budget=5)
        assert trimmed is True
        assert result[0] == system

    def test_system_message_not_counted_in_dropped_pairs(self):
        system = {"role": "system", "content": "s"}
        msgs = [system] + _msgs(2, chars_per_msg=4)
        result, _ = trim_history(msgs, budget=1000)
        assert system in result

    def test_was_trimmed_false_when_exact_budget(self):
        # 1 pair × 2 × 4 chars = 8 chars → 2 tokens
        msgs = _msgs(1, chars_per_msg=4)
        _, trimmed = trim_history(msgs, budget=2)
        assert trimmed is False


# ── Orchestrator integration ──────────────────────────────────────────────────


def _make_orchestrator(mocker):
    mocker.patch("src.orchestrator.OllamaRouter")
    mocker.patch("src.orchestrator.OpenRouterClient")
    mocker.patch("src.orchestrator.MemoryStore")
    return Orchestrator(memory_enabled=False)


class TestOrchestratorTrimming:
    def _long_history(self, n_pairs: int, chars: int = 200) -> list[dict]:
        msgs = []
        for _ in range(n_pairs):
            msgs.append({"role": "user", "content": "u" * chars})
            msgs.append({"role": "assistant", "content": "a" * chars})
        return msgs

    def test_trim_note_appended_when_trimmed(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])
        mocker.patch.object(orch, "_ollama_respond", return_value="reply")
        # Force a very small budget so trimming must occur
        mocker.patch.dict(
            "src.orchestrator._MODEL_CONFIG",
            {"trivial_llm": type("MC", (), {"context_tokens": 1})()},
        )
        history = self._long_history(5)
        response, _ = orch.respond("hi", history)
        assert "trimmed" in response

    def test_no_trim_note_when_within_budget(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])
        mocker.patch.object(orch, "_ollama_respond", return_value="reply")
        mocker.patch.dict(
            "src.orchestrator._MODEL_CONFIG",
            {"trivial_llm": type("MC", (), {"context_tokens": 100000})()},
        )
        response, _ = orch.respond("hi", [])
        assert "trimmed" not in response

    def test_history_within_budget_unchanged(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])
        captured = {}

        def _capture(query, augmented, model, **kw):
            captured["augmented"] = augmented
            return "reply"

        mocker.patch.object(orch, "_ollama_respond", side_effect=_capture)
        mocker.patch.dict(
            "src.orchestrator._MODEL_CONFIG",
            {"trivial_llm": type("MC", (), {"context_tokens": 100000})()},
        )
        history = [{"role": "user", "content": "hi"}]
        orch.respond("follow-up", history)
        # augmented should contain the history message
        contents = [m.get("content") for m in captured["augmented"]]
        assert "hi" in contents

    def test_stream_respond_trim_note_on_final_yield(self, mocker):
        orch = _make_orchestrator(mocker)
        orch._router.classify.return_value = "trivial_llm"
        mocker.patch("src.orchestrator.REGISTRY.dispatch", return_value=None)
        mocker.patch("src.orchestrator.REGISTRY.schemas", return_value=[])
        mocker.patch.object(
            orch,
            "_ollama_stream",
            return_value=iter(["reply"]),
        )
        mocker.patch.dict(
            "src.orchestrator._MODEL_CONFIG",
            {"trivial_llm": type("MC", (), {"context_tokens": 1})()},
        )
        history = self._long_history(5)
        yields = list(orch.stream_respond("hi", history))
        final_text, _ = yields[-1]
        assert "trimmed" in final_text
