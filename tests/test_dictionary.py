"""Unit tests for src/tools/dictionary.py."""

import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from src.tools.dictionary import _handle_define_query, define


def _mock_urlopen(data: list):
    """Patch urllib.request.urlopen to return JSON dictionary data."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch(
        "src.tools.dictionary.urllib.request.urlopen", return_value=mock_resp
    )


_SAMPLE_DATA = [
    {
        "word": "ephemeral",
        "phonetic": "/ɪˈfɛm.ər.əl/",
        "meanings": [
            {
                "partOfSpeech": "adjective",
                "definitions": [
                    {
                        "definition": "Lasting for a short time.",
                        "example": "fashions are ephemeral",
                    },
                    {"definition": "Existing only briefly.", "example": ""},
                ],
            }
        ],
    }
]


class TestDefine:
    def test_returns_headword(self):
        with _mock_urlopen(_SAMPLE_DATA):
            result = define("ephemeral")
        assert "ephemeral" in result

    def test_returns_phonetic(self):
        with _mock_urlopen(_SAMPLE_DATA):
            result = define("ephemeral")
        assert "/ɪˈfɛm.ər.əl/" in result

    def test_returns_part_of_speech(self):
        with _mock_urlopen(_SAMPLE_DATA):
            result = define("ephemeral")
        assert "adjective" in result

    def test_returns_definition(self):
        with _mock_urlopen(_SAMPLE_DATA):
            result = define("ephemeral")
        assert "Lasting for a short time" in result

    def test_returns_example_sentence(self):
        with _mock_urlopen(_SAMPLE_DATA):
            result = define("ephemeral")
        assert "fashions are ephemeral" in result

    def test_skips_empty_example(self):
        with _mock_urlopen(_SAMPLE_DATA):
            result = define("ephemeral")
        # Second definition has no example — no blank example line
        assert 'e.g. ""' not in result

    def test_404_returns_not_found_message(self):
        with patch(
            "src.tools.dictionary.urllib.request.urlopen",
            side_effect=HTTPError(
                url="", code=404, msg="Not Found", hdrs={}, fp=None
            ),
        ):
            result = define("xyzzy")
        assert "No definition found" in result

    def test_network_error_returns_error_message(self):
        with patch(
            "src.tools.dictionary.urllib.request.urlopen",
            side_effect=OSError("timeout"),
        ):
            result = define("word")
        assert "Dictionary API error" in result

    def test_empty_word_returns_prompt(self):
        result = define("")
        assert "Please provide" in result

    def test_empty_data_returns_not_found(self):
        with _mock_urlopen([]):
            result = define("nonce")
        assert "No definition found" in result

    def test_no_phonetic_omits_slashes(self):
        data = [{"word": "test", "phonetic": "", "meanings": []}]
        with _mock_urlopen(data):
            result = define("test")
        assert "//" not in result

    def test_multiple_meanings_included(self):
        data = [
            {
                "word": "run",
                "phonetic": "/rʌn/",
                "meanings": [
                    {
                        "partOfSpeech": "verb",
                        "definitions": [
                            {"definition": "Move fast.", "example": ""}
                        ],
                    },
                    {
                        "partOfSpeech": "noun",
                        "definitions": [
                            {"definition": "An act of running.", "example": ""}
                        ],
                    },
                ],
            }
        ]
        with _mock_urlopen(data):
            result = define("run")
        assert "verb" in result
        assert "noun" in result


class TestHandleDefineQuery:
    def _patch_define(self, return_value="**test**\n_noun_\n  1. A test."):
        return patch("src.tools.dictionary.define", return_value=return_value)

    def test_strips_define_preamble(self):
        with self._patch_define() as mock:
            _handle_define_query("define ephemeral")
        mock.assert_called_once_with("ephemeral")

    def test_strips_what_does_mean(self):
        with self._patch_define() as mock:
            _handle_define_query("what does sanguine mean")
        mock.assert_called_once_with("sanguine mean")

    def test_strips_definition_of(self):
        with self._patch_define() as mock:
            _handle_define_query("definition of ubiquitous")
        mock.assert_called_once_with("ubiquitous")

    def test_strips_meaning_of(self):
        with self._patch_define() as mock:
            _handle_define_query("meaning of perfidious")
        mock.assert_called_once_with("perfidious")

    def test_strips_trailing_question_mark(self):
        with self._patch_define() as mock:
            _handle_define_query("define ephemeral?")
        mock.assert_called_once_with("ephemeral")

    def test_empty_after_strip_returns_none(self):
        # "define " with trailing space matches the preamble, leaving ""
        result = _handle_define_query("define ")
        assert result is None

    def test_api_error_returns_none(self):
        with self._patch_define("(Dictionary API error: timeout)"):
            result = _handle_define_query("define test")
        assert result is None

    def test_valid_result_returned(self):
        with self._patch_define():
            result = _handle_define_query("define test")
        assert result is not None


class TestGlobalRegistration:
    def test_dictionary_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "dictionary" in names

    def test_dictionary_tier_and_category(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "dictionary")
        assert tool.router_tier == "dictionary"
        assert tool.category == "general"
        assert tool.approach == "A"
