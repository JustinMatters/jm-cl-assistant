"""Unit tests for src/tools/currency.py."""

import json
from unittest.mock import MagicMock, patch

import pytest

import src.tools.currency as currency_mod
from src.tools.currency import (
    _fetch_rate,
    _handle_currency_query,
    _resolve_code,
    convert_currency,
)


@pytest.fixture(autouse=True)
def clear_rate_cache():
    """Reset the session rate cache before each test."""
    currency_mod._rate_cache.clear()
    yield
    currency_mod._rate_cache.clear()


def _mock_urlopen(rate: float, date: str = "2026-04-05", to_code: str = "EUR"):
    """Patch urllib.request.urlopen to return a Frankfurter-style response."""
    data = {"rates": {to_code: rate}, "date": date}
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch(
        "src.tools.currency.urllib.request.urlopen", return_value=mock_resp
    )


class TestResolveCode:
    def test_uppercase_code_returned(self):
        assert _resolve_code("USD") == "USD"

    def test_lowercase_code_resolved(self):
        assert _resolve_code("usd") == "USD"

    def test_currency_name_resolved(self):
        assert _resolve_code("dollars") == "USD"
        assert _resolve_code("euros") == "EUR"
        assert _resolve_code("pounds") == "GBP"
        assert _resolve_code("yen") == "JPY"

    def test_unknown_returns_none(self):
        assert _resolve_code("groats") is None

    def test_mixed_case_code(self):
        assert _resolve_code("Gbp") == "GBP"


class TestFetchRate:
    def test_returns_rate_and_date(self):
        with _mock_urlopen(0.9147):
            result = _fetch_rate("USD", "EUR")
        assert result is not None
        rate, date = result
        assert rate == pytest.approx(0.9147)
        assert date == "2026-04-05"

    def test_result_is_cached(self):
        with _mock_urlopen(0.9147) as mock_open:
            _fetch_rate("USD", "EUR")
            _fetch_rate("USD", "EUR")
        assert mock_open.call_count == 1

    def test_network_error_returns_none(self):
        with patch(
            "src.tools.currency.urllib.request.urlopen",
            side_effect=OSError("timeout"),
        ):
            result = _fetch_rate("USD", "EUR")
        assert result is None

    def test_missing_rate_in_response_returns_none(self):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(
            {"rates": {}, "date": "x"}
        ).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        with patch(
            "src.tools.currency.urllib.request.urlopen", return_value=mock_resp
        ):
            result = _fetch_rate("USD", "EUR")
        assert result is None


class TestConvertCurrency:
    def test_basic_conversion(self):
        with _mock_urlopen(0.9147):
            result = convert_currency(100.0, "USD", "EUR")
        assert "100.00 USD" in result
        assert "91.47 EUR" in result
        assert "0.9147" in result

    def test_includes_date(self):
        with _mock_urlopen(0.9147, date="2026-04-05"):
            result = convert_currency(100.0, "USD", "EUR")
        assert "2026-04-05" in result

    def test_same_currency_no_api_call(self):
        result = convert_currency(50.0, "USD", "USD")
        assert "50.00 USD" in result

    def test_unsupported_from_currency(self):
        result = convert_currency(100.0, "XYZ", "EUR")
        assert "Unsupported" in result

    def test_unsupported_to_currency(self):
        result = convert_currency(100.0, "USD", "XYZ")
        assert "Unsupported" in result

    def test_api_failure_returns_error(self):
        with patch(
            "src.tools.currency.urllib.request.urlopen",
            side_effect=OSError("fail"),
        ):
            result = convert_currency(100.0, "USD", "EUR")
        assert "Could not fetch" in result

    def test_lowercase_codes_accepted(self):
        with _mock_urlopen(0.9147):
            result = convert_currency(100.0, "usd", "eur")
        assert "USD" in result
        assert "EUR" in result


class TestHandleCurrencyQuery:
    def _patch_convert(self, return_value="100.00 USD = 91.47 EUR"):
        return patch(
            "src.tools.currency.convert_currency", return_value=return_value
        )

    def test_parses_convert_usd_to_eur(self):
        with self._patch_convert() as mock:
            _handle_currency_query("convert 100 USD to EUR")
        mock.assert_called_once_with(100.0, "USD", "EUR")

    def test_parses_amount_name_to_code(self):
        with self._patch_convert() as mock:
            _handle_currency_query("100 dollars to EUR")
        mock.assert_called_once_with(100.0, "USD", "EUR")

    def test_parses_in_keyword(self):
        with self._patch_convert() as mock:
            _handle_currency_query("50 GBP in USD")
        mock.assert_called_once_with(50.0, "GBP", "USD")

    def test_parses_decimal_amount(self):
        with self._patch_convert() as mock:
            _handle_currency_query("1.5 GBP to USD")
        mock.assert_called_once_with(1.5, "GBP", "USD")

    def test_parses_comma_in_amount(self):
        with self._patch_convert() as mock:
            _handle_currency_query("1,000 USD to EUR")
        mock.assert_called_once_with(1000.0, "USD", "EUR")

    def test_unrecognised_currency_returns_none(self):
        result = _handle_currency_query("100 groats to USD")
        assert result is None

    def test_unparseable_query_returns_none(self):
        result = _handle_currency_query("what is the weather")
        assert result is None


class TestGlobalRegistration:
    def test_currency_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "currency" in names

    def test_currency_tier_and_category(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "currency")
        assert tool.router_tier == "currency"
        assert tool.category == "web"
        assert tool.approach == "A"
