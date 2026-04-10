"""Unit tests for Phase 25 — Conversation Export (T25.3).

Covers: empty history, user/assistant formatting, special Markdown
characters preserved, system messages excluded, timestamp header present.
"""

import pytest

helpers_module = pytest.importorskip("src.helpers")
format_history_as_markdown = helpers_module.format_history_as_markdown


class TestFormatHistoryAsMarkdown:
    def test_empty_history_returns_header(self):
        result = format_history_as_markdown([])
        assert "# Conversation Export" in result

    def test_empty_history_contains_timestamp(self):
        result = format_history_as_markdown([])
        assert "_Exported:" in result

    def test_empty_history_no_user_or_assistant_blocks(self):
        result = format_history_as_markdown([])
        assert "**User:**" not in result
        assert "**Assistant:**" not in result

    def test_user_turn_formatted_correctly(self):
        history = [{"role": "user", "content": "Hello there"}]
        result = format_history_as_markdown(history)
        assert "**User:** Hello there" in result

    def test_assistant_turn_formatted_correctly(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        result = format_history_as_markdown(history)
        assert "**Assistant:** Hello!" in result

    def test_horizontal_rule_separates_turns(self):
        history = [
            {"role": "user", "content": "Q1"},
            {"role": "assistant", "content": "A1"},
            {"role": "user", "content": "Q2"},
            {"role": "assistant", "content": "A2"},
        ]
        result = format_history_as_markdown(history)
        assert result.count("---") >= 2

    def test_system_messages_excluded(self):
        history = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello"},
        ]
        result = format_history_as_markdown(history)
        assert "You are helpful." not in result

    def test_markdown_special_chars_preserved(self):
        content = "**bold** and `code` and [link](url)"
        history = [
            {"role": "user", "content": content},
            {"role": "assistant", "content": content},
        ]
        result = format_history_as_markdown(history)
        assert "**bold**" in result
        assert "`code`" in result
        assert "[link](url)" in result

    def test_multi_turn_order_preserved(self):
        history = [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "one"},
            {"role": "user", "content": "second"},
            {"role": "assistant", "content": "two"},
        ]
        result = format_history_as_markdown(history)
        assert result.index("first") < result.index("second")
        assert result.index("one") < result.index("two")

    def test_returns_string(self):
        result = format_history_as_markdown([])
        assert isinstance(result, str)

    def test_result_ends_with_newline(self):
        result = format_history_as_markdown([])
        assert result.endswith("\n")

    def test_none_content_handled(self):
        history = [{"role": "user", "content": None}]
        result = format_history_as_markdown(history)
        assert "**User:**" in result
