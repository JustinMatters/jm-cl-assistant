"""Unit tests for src/tools/url_reader.py."""

from unittest.mock import patch

from src.tools.url_reader import (
    _sanitise,
    _url_reader_callable,
    _validate_url,
    summarise_url,
)


class TestValidateUrl:
    def test_valid_https_url(self):
        assert _validate_url("https://example.com") == "https://example.com"

    def test_valid_http_url(self):
        assert _validate_url("http://example.com/page") is not None

    def test_rejects_ftp_scheme(self):
        assert _validate_url("ftp://example.com/file") is None

    def test_rejects_file_scheme(self):
        assert _validate_url("file:///etc/passwd") is None

    def test_rejects_no_netloc(self):
        assert _validate_url("https://") is None

    def test_strips_whitespace(self):
        result = _validate_url("  https://example.com  ")
        assert result == "https://example.com"


class TestSanitise:
    def test_plain_text_unchanged(self):
        assert _sanitise("hello world", 200) == "hello world"

    def test_strips_control_chars(self):
        assert _sanitise("ab\x00cd", 200) == "abcd"

    def test_preserves_newlines(self):
        result = _sanitise("line one\nline two", 200)
        assert "\n" in result

    def test_truncates_at_paragraph_boundary(self):
        text = "First para.\n\nSecond para.\n\nThird para."
        result = _sanitise(text, 20)
        assert "First para." in result
        assert "Third para." not in result

    def test_truncates_with_ellipsis(self):
        result = _sanitise("abcdefghij", 5)
        assert result.endswith("\u2026")

    def test_strips_edges(self):
        assert _sanitise("  hello  ", 200) == "hello"


class TestSummariseUrl:
    def _patch_trafilatura(
        self, downloaded="<html/>", extracted="Article text."
    ):
        fetch = patch(
            "src.tools.url_reader.trafilatura.fetch_url",
            return_value=downloaded,
        )
        extract = patch(
            "src.tools.url_reader.trafilatura.extract",
            return_value=extracted,
        )
        return fetch, extract

    def test_returns_content_with_url_header(self):
        fetch, extract = self._patch_trafilatura()
        with fetch, extract:
            result = summarise_url("https://example.com")
        assert "Content extracted from https://example.com" in result
        assert "Article text." in result

    def test_includes_source_footer(self):
        fetch, extract = self._patch_trafilatura()
        with fetch, extract:
            result = summarise_url("https://example.com")
        assert "(Source: https://example.com)" in result

    def test_invalid_url_returns_error(self):
        result = summarise_url("ftp://bad.url")
        assert "Invalid or unsupported URL" in result

    def test_fetch_failure_returns_error(self):
        with patch(
            "src.tools.url_reader.trafilatura.fetch_url",
            side_effect=OSError("timeout"),
        ):
            result = summarise_url("https://example.com")
        assert "URL fetch error" in result

    def test_empty_download_returns_error(self):
        with patch(
            "src.tools.url_reader.trafilatura.fetch_url", return_value=None
        ):
            result = summarise_url("https://example.com")
        assert "Could not fetch" in result

    def test_no_extracted_text_returns_error(self):
        fetch, extract = self._patch_trafilatura(extracted=None)
        with fetch, extract:
            result = summarise_url("https://example.com")
        assert "No readable text" in result

    def test_content_sanitised(self):
        fetch, extract = self._patch_trafilatura(extracted="Text\x00with null.")
        with fetch, extract:
            result = summarise_url("https://example.com")
        assert "\x00" not in result


class TestUrlReaderCallable:
    def _patch_summarise(self, return_value="Content extracted from ..."):
        return patch(
            "src.tools.url_reader.summarise_url", return_value=return_value
        )

    def test_parses_url_and_calls_summarise(self):
        with self._patch_summarise() as mock:
            result = _url_reader_callable('{"url": "https://example.com"}')
        mock.assert_called_once_with("https://example.com")
        assert result is not None

    def test_invalid_json_returns_none(self):
        assert _url_reader_callable("not json") is None

    def test_empty_url_returns_none(self):
        assert _url_reader_callable('{"url": ""}') is None

    def test_missing_url_key_returns_none(self):
        assert _url_reader_callable('{"link": "https://x.com"}') is None

    def test_fetch_error_returns_none(self):
        with self._patch_summarise("(URL fetch error: timeout)"):
            result = _url_reader_callable('{"url": "https://example.com"}')
        assert result is None

    def test_valid_result_returned(self):
        with self._patch_summarise():
            result = _url_reader_callable('{"url": "https://example.com"}')
        assert result is not None


class TestGlobalRegistration:
    def test_url_reader_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "url_reader" in names

    def test_url_reader_approach_b(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "url_reader")
        assert tool.approach == "B"
        assert tool.min_tier == "advanced_llm"
        assert tool.parameters_schema is not None

    def test_url_reader_not_in_router_prompt(self):
        from src.tools.registry import REGISTRY

        section = REGISTRY.router_prompt_section({"url_reader"})
        assert "url_reader" not in section
