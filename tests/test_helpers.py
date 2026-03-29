import pytest

helpers_module = pytest.importorskip("src.helpers")
strip_think_tags = helpers_module.strip_think_tags


class TestStripThinkTags:
    def test_strips_think_block(self):
        text = "<think>internal reasoning</think>Final answer."
        assert strip_think_tags(text) == "Final answer."

    def test_no_think_tags_unchanged(self):
        text = "Just a plain response."
        assert strip_think_tags(text) == "Just a plain response."

    def test_strips_multiline_think_block(self):
        text = "<think>\nline one\nline two\n</think>The answer is 42."
        assert strip_think_tags(text) == "The answer is 42."

    def test_strips_multiple_think_blocks(self):
        text = "<think>first</think>middle<think>second</think>end"
        result = strip_think_tags(text)
        assert "middle" in result
        assert "end" in result
        assert "<think>" not in result

    def test_empty_think_block_stripped(self):
        text = "<think></think>Response."
        assert strip_think_tags(text) == "Response."

    def test_think_only_returns_empty_string(self):
        text = "<think>nothing to see</think>"
        assert strip_think_tags(text) == ""

    def test_whitespace_trimmed_after_strip(self):
        text = "<think>reasoning</think>   trimmed   "
        assert strip_think_tags(text) == "trimmed"
