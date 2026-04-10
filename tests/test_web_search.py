"""Unit tests for src/tools/web_search.py."""

from unittest.mock import patch

from src.tools.web_search import _handle_web_search_query, _sanitise, web_search


class TestSanitise:
    def test_plain_text_unchanged(self):
        assert _sanitise("hello world", 200) == "hello world"

    def test_strips_control_characters(self):
        # \x00 is Cc (control), \x08 is backspace (Cc)
        assert _sanitise("ab\x00cd\x08ef", 200) == "abcdef"

    def test_strips_format_characters(self):
        # U+200B zero-width space is Cf (format)
        assert _sanitise("ab\u200bcd", 200) == "abcd"

    def test_preserves_spaces(self):
        assert _sanitise("hello world", 200) == "hello world"

    def test_truncates_to_max_len(self):
        result = _sanitise("a" * 50, 10)
        assert len(result) == 11  # 10 chars + ellipsis
        assert result.endswith("\u2026")

    def test_no_truncation_at_exact_length(self):
        result = _sanitise("a" * 10, 10)
        assert result == "a" * 10

    def test_strips_whitespace_from_edges(self):
        assert _sanitise("  hello  ", 200) == "hello"


class TestWebSearch:
    def _make_result(
        self, title="Title", body="Snippet", href="https://example.com"
    ):
        return {"title": title, "body": body, "href": href}

    def test_returns_formatted_results(self):
        mock_results = [self._make_result()]
        with patch("src.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = (
                mock_results
            )
            output = web_search("python news")
        assert "1." in output
        assert "Title" in output
        assert "Snippet" in output
        assert "https://example.com" in output

    def test_multiple_results_numbered(self):
        mock_results = [
            self._make_result(title="First"),
            self._make_result(title="Second"),
        ]
        with patch("src.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = (
                mock_results
            )
            output = web_search("query")
        assert "1." in output
        assert "2." in output

    def test_empty_results_returns_no_results_message(self):
        with patch("src.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = []
            output = web_search("nothing")
        assert output == "No results found."

    def test_exception_returns_error_message(self):
        with patch("src.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.side_effect = RuntimeError(
                "timeout"
            )
            output = web_search("query")
        assert output.startswith("(Web search error:")
        assert "timeout" in output

    def test_output_truncated_at_max(self):
        long_snippet = "x" * 400
        mock_results = [self._make_result(body=long_snippet)] * 5
        with patch("src.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = (
                mock_results
            )
            output = web_search("query", max_results=5)
        assert len(output) <= 1502  # 1500 + newline + ellipsis

    def test_missing_fields_handled_gracefully(self):
        with patch("src.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = [
                {}
            ]
            output = web_search("query")
        assert "1." in output  # should not raise

    def test_sanitises_control_chars_in_results(self):
        mock_results = [self._make_result(title="Good\x00Title")]
        with patch("src.tools.web_search.DDGS") as mock_ddgs:
            mock_ddgs.return_value.__enter__.return_value.text.return_value = (
                mock_results
            )
            output = web_search("query")
        assert "\x00" not in output
        assert "GoodTitle" in output


class TestHandleWebSearchQuery:
    def _mock_search(self, return_value="result"):
        return patch(
            "src.tools.web_search.web_search", return_value=return_value
        )

    def test_passes_cleaned_query_to_search(self):
        with self._mock_search() as mock:
            _handle_web_search_query("search for python news")
        mock.assert_called_once_with("python news")

    def test_strips_look_up_preamble(self):
        with self._mock_search() as mock:
            _handle_web_search_query("look up the weather")
        mock.assert_called_once_with("the weather")

    def test_strips_find_preamble(self):
        with self._mock_search() as mock:
            _handle_web_search_query("find information about pandas")
        mock.assert_called_once_with("pandas")

    def test_strips_google_preamble(self):
        with self._mock_search() as mock:
            _handle_web_search_query("google latest news")
        mock.assert_called_once_with("latest news")

    def test_no_preamble_passes_query_unchanged(self):
        with self._mock_search() as mock:
            _handle_web_search_query("Python 3.13 release notes")
        mock.assert_called_once_with("Python 3.13 release notes")

    def test_blank_query_after_stripping_returns_none(self):
        result = _handle_web_search_query("search for")
        assert result is None

    def test_error_result_returns_none(self):
        with self._mock_search("(Web search error: timeout)"):
            result = _handle_web_search_query("anything")
        assert result is None

    def test_valid_result_returned(self):
        with self._mock_search("1. Title\n   Snippet\n   https://example.com"):
            result = _handle_web_search_query("python news")
        assert result is not None
        assert "Title" in result


class TestGlobalRegistration:
    def test_web_search_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "web_search" in names

    def test_web_search_tier(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "web_search")
        assert tool.router_tier == "web_search"
        assert tool.category == "web"
        assert tool.approach == "A"
