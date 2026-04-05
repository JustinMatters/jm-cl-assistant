"""Unit tests for src/tools/wikipedia.py."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from src.tools.wikipedia import _sanitise, _wiki_callable, wiki_summary


def _mock_urlopen(data: dict):
    """Patch urllib.request.urlopen to return JSON Wikipedia data."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch(
        "src.tools.wikipedia.urllib.request.urlopen", return_value=mock_resp
    )


_SAMPLE_DATA = {
    "title": "Alan Turing",
    "extract": (
        "Alan Mathison Turing was an English mathematician and computer "
        "scientist. Turing was highly influential in the development of "
        "theoretical computer science."
    ),
    "content_urls": {
        "desktop": {"page": "https://en.wikipedia.org/wiki/Alan_Turing"}
    },
}


class TestSanitise:
    def test_plain_text_unchanged(self):
        assert _sanitise("hello world", 200) == "hello world"

    def test_strips_control_chars(self):
        assert _sanitise("ab\x00cd", 200) == "abcd"

    def test_strips_format_chars(self):
        assert _sanitise("ab\u200bcd", 200) == "abcd"

    def test_truncates_at_sentence_boundary(self):
        text = "First sentence. Second sentence. Third sentence extra words."
        result = _sanitise(text, 35)
        assert result.endswith(".")
        assert "First sentence." in result

    def test_truncates_with_ellipsis_when_no_boundary(self):
        text = "abcdefghij"
        result = _sanitise(text, 5)
        assert result.endswith("\u2026")

    def test_strips_edges(self):
        assert _sanitise("  hello  ", 200) == "hello"


class TestWikiSummary:
    def test_returns_title_and_extract(self):
        with _mock_urlopen(_SAMPLE_DATA):
            result = wiki_summary("Alan Turing")
        assert "Alan Turing" in result
        assert "mathematician" in result

    def test_includes_url(self):
        with _mock_urlopen(_SAMPLE_DATA):
            result = wiki_summary("Alan Turing")
        assert "wikipedia.org" in result

    def test_404_returns_not_found(self):
        with patch(
            "src.tools.wikipedia.urllib.request.urlopen",
            side_effect=HTTPError(
                url="", code=404, msg="Not Found", hdrs={}, fp=None
            ),
        ):
            result = wiki_summary("XyzzyNonexistent")
        assert "No Wikipedia article found" in result

    def test_network_error_returns_error_message(self):
        with patch(
            "src.tools.wikipedia.urllib.request.urlopen",
            side_effect=OSError("timeout"),
        ):
            result = wiki_summary("anything")
        assert "Wikipedia API error" in result

    def test_empty_extract_returns_no_summary(self):
        data = {**_SAMPLE_DATA, "extract": ""}
        with _mock_urlopen(data):
            result = wiki_summary("Alan Turing")
        assert "No summary available" in result

    def test_missing_url_omits_link(self):
        data = {**_SAMPLE_DATA, "content_urls": {}}
        with _mock_urlopen(data):
            result = wiki_summary("Alan Turing")
        assert "wikipedia.org" not in result
        assert "Alan Turing" in result

    def test_extract_sanitised(self):
        data = {**_SAMPLE_DATA, "extract": "Good text\x00 with nulls."}
        with _mock_urlopen(data):
            result = wiki_summary("test")
        assert "\x00" not in result


class TestWikiCallable:
    def _patch_wiki(self, return_value="Alan Turing: mathematician..."):
        return patch(
            "src.tools.wikipedia.wiki_summary", return_value=return_value
        )

    def test_parses_topic_and_calls_wiki_summary(self):
        with self._patch_wiki() as mock:
            result = _wiki_callable('{"topic": "Alan Turing"}')
        mock.assert_called_once_with("Alan Turing")
        assert result is not None

    def test_invalid_json_returns_none(self):
        result = _wiki_callable("not json at all")
        assert result is None

    def test_empty_topic_returns_none(self):
        result = _wiki_callable('{"topic": ""}')
        assert result is None

    def test_missing_topic_key_returns_none(self):
        result = _wiki_callable('{"query": "something"}')
        assert result is None

    def test_api_error_returns_none(self):
        with self._patch_wiki("(Wikipedia API error: timeout)"):
            result = _wiki_callable('{"topic": "test"}')
        assert result is None

    def test_valid_result_returned(self):
        with self._patch_wiki():
            result = _wiki_callable('{"topic": "Python"}')
        assert result is not None


class TestRouterPromptExclusion:
    """Approach B tools must not appear in the router prompt."""

    def test_wikipedia_excluded_from_router_prompt(self):
        from src.tools.registry import REGISTRY

        section = REGISTRY.router_prompt_section({"wikipedia"})
        assert "wikipedia" not in section.lower()


class TestGlobalRegistration:
    def test_wikipedia_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "wikipedia" in names

    def test_wikipedia_approach_b(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "wikipedia")
        assert tool.approach == "B"
        assert tool.parameters_schema is not None
        assert "topic" in tool.parameters_schema["properties"]

    def test_wikipedia_in_schemas(self):
        from src.tools.registry import REGISTRY

        schemas = REGISTRY.schemas({"wikipedia"})
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "wikipedia"
