"""Unit tests for src/tools/location.py."""

from unittest.mock import MagicMock, patch

import pytest

import src.tools.location as location_mod
from src.tools.location import (
    _handle_location_query,
    get_location,
    get_location_str,
)


@pytest.fixture(autouse=True)
def clear_cache():
    """Reset the module-level location cache before each test."""
    location_mod._cache = None
    yield
    location_mod._cache = None


def _mock_urlopen(data: dict):
    """Return a context manager mock that yields a response with JSON data."""
    import json

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch(
        "src.tools.location.urllib.request.urlopen", return_value=mock_resp
    )


_SUCCESS_DATA = {
    "status": "success",
    "city": "London",
    "regionName": "England",
    "country": "United Kingdom",
    "countryCode": "GB",
    "lat": 51.5074,
    "lon": -0.1278,
}


class TestGetLocation:
    def test_returns_location_dict_on_success(self):
        with _mock_urlopen(_SUCCESS_DATA):
            result = get_location()
        assert result["city"] == "London"
        assert result["region"] == "England"
        assert result["country"] == "United Kingdom"
        assert result["country_code"] == "GB"
        assert result["lat"] == pytest.approx(51.5074)
        assert result["lon"] == pytest.approx(-0.1278)

    def test_returns_error_on_api_failure_status(self):
        with _mock_urlopen({"status": "fail", "message": "reserved range"}):
            result = get_location()
        assert "error" in result
        assert "reserved range" in result["error"]

    def test_returns_error_on_network_exception(self):
        with patch(
            "src.tools.location.urllib.request.urlopen",
            side_effect=OSError("timeout"),
        ):
            result = get_location()
        assert "error" in result
        assert "timeout" in result["error"]

    def test_result_is_cached_after_first_call(self):
        with _mock_urlopen(_SUCCESS_DATA) as mock_open:
            get_location()
            get_location()
        assert mock_open.call_count == 1

    def test_cache_cleared_by_fixture(self):
        # Verify the autouse fixture resets cache between tests.
        assert location_mod._cache is None


class TestGetLocationStr:
    def test_returns_formatted_string(self):
        with _mock_urlopen(_SUCCESS_DATA):
            result = get_location_str()
        assert result == "London, England, GB"

    def test_returns_unavailable_on_error(self):
        with patch(
            "src.tools.location.urllib.request.urlopen",
            side_effect=OSError("fail"),
        ):
            result = get_location_str()
        assert result == "Location unavailable"

    def test_skips_empty_parts(self):
        data = {**_SUCCESS_DATA, "city": "", "regionName": ""}
        with _mock_urlopen(data):
            result = get_location_str()
        assert result == "GB"


class TestHandleLocationQuery:
    def test_returns_location_with_coords(self):
        with _mock_urlopen(_SUCCESS_DATA):
            result = _handle_location_query("where am I")
        assert "London" in result
        assert "England" in result
        assert "GB" in result
        assert "51.5074" in result
        assert "-0.1278" in result

    def test_returns_error_message_on_failure(self):
        with patch(
            "src.tools.location.urllib.request.urlopen",
            side_effect=OSError("no network"),
        ):
            result = _handle_location_query("where am I")
        assert "Could not determine location" in result
        assert "no network" in result

    def test_query_arg_ignored(self):
        with _mock_urlopen(_SUCCESS_DATA):
            r1 = _handle_location_query("where am I")
            r2 = _handle_location_query("what city")
        assert r1 == r2


class TestGlobalRegistration:
    def test_location_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "location" in names

    def test_location_tier_and_category(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "location")
        assert tool.router_tier == "location"
        assert tool.category == "web"
        assert tool.approach == "A"
