import io
import wave

import numpy as np
import pytest

helpers_module = pytest.importorskip("src.helpers")
strip_markdown = helpers_module.strip_markdown
strip_think_tags = helpers_module.strip_think_tags
to_wav_bytes = helpers_module.to_wav_bytes


class TestStripMarkdown:
    def test_bold_asterisks_removed(self):
        assert strip_markdown("**bold**") == "bold"

    def test_italic_asterisk_removed(self):
        assert strip_markdown("*italic*") == "italic"

    def test_bold_italic_removed(self):
        assert strip_markdown("***bold italic***") == "bold italic"

    def test_bold_underscores_removed(self):
        assert strip_markdown("__bold__") == "bold"

    def test_italic_underscore_removed(self):
        assert strip_markdown("_italic_") == "italic"

    def test_heading_hash_removed(self):
        assert strip_markdown("## Heading") == "Heading"

    def test_inline_code_removed(self):
        assert strip_markdown("`code`") == ""

    def test_fenced_code_block_removed(self):
        assert strip_markdown("```\nsome code\n```").strip() == ""

    def test_link_text_kept_url_removed(self):
        result = strip_markdown("[click here](https://example.com)")
        assert result == "click here"

    def test_blockquote_marker_removed(self):
        assert strip_markdown("> quoted text") == "quoted text"

    def test_horizontal_rule_removed(self):
        assert strip_markdown("---") == ""

    def test_plain_text_unchanged(self):
        assert strip_markdown("Hello world.") == "Hello world."

    def test_mixed_response(self):
        text = "**Summary:** the answer is _important_ and `x = 1`."
        result = strip_markdown(text)
        assert "Summary:" in result
        assert "important" in result
        assert "**" not in result
        assert "_" not in result
        assert "`" not in result


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


class TestToWavBytes:
    def test_returns_bytes(self):
        arr = np.zeros(100, dtype=np.float32)
        result = to_wav_bytes(arr, 24000)
        assert isinstance(result, bytes)

    def test_output_is_valid_wav(self):
        arr = np.zeros(100, dtype=np.float32)
        result = to_wav_bytes(arr, 24000)
        with wave.open(io.BytesIO(result), "rb") as wf:
            assert wf.getsampwidth() == 2  # int16
            assert wf.getnchannels() == 1  # mono
            assert wf.getframerate() == 24000

    def test_sample_rate_is_preserved(self):
        arr = np.zeros(100, dtype=np.float32)
        result = to_wav_bytes(arr, 22050)
        with wave.open(io.BytesIO(result), "rb") as wf:
            assert wf.getframerate() == 22050

    def test_values_clipped_before_conversion(self):
        arr = np.array([2.0, -2.0, 0.5], dtype=np.float32)
        result = to_wav_bytes(arr, 24000)
        with wave.open(io.BytesIO(result), "rb") as wf:
            raw = wf.readframes(wf.getnframes())
        samples = np.frombuffer(raw, dtype=np.int16)
        assert samples[0] == 32767
        assert samples[1] == -32767

    def test_2d_array_flattened_to_mono(self):
        arr = np.zeros((100, 1), dtype=np.float32)
        result = to_wav_bytes(arr, 24000)
        with wave.open(io.BytesIO(result), "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getnframes() == 100
