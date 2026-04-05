"""Unit tests for src/tools/datetime_tool.py."""

from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from src.tools.datetime_tool import (
    _format_dt,
    _handle_datetime_query,
    _resolve_timezone,
    get_datetime,
)


class TestFormatDt:
    def test_formats_known_datetime(self):
        dt = datetime(2026, 4, 5, 14, 35, tzinfo=ZoneInfo("Europe/London"))
        result = _format_dt(dt)
        assert "Sunday" in result
        assert "5" in result
        assert "April" in result
        assert "2026" in result
        assert "14:35" in result

    def test_no_leading_zero_on_day(self):
        dt = datetime(2026, 4, 5, 9, 0, tzinfo=ZoneInfo("UTC"))
        result = _format_dt(dt)
        assert " 5 " in result
        assert " 05 " not in result

    def test_includes_timezone_abbreviation(self):
        dt = datetime(2026, 4, 5, 14, 0, tzinfo=ZoneInfo("UTC"))
        result = _format_dt(dt)
        assert "UTC" in result


class TestResolveTimezone:
    def test_city_name_resolves(self):
        tz = _resolve_timezone("Tokyo")
        assert tz is not None
        assert tz.key == "Asia/Tokyo"

    def test_city_name_case_insensitive(self):
        tz = _resolve_timezone("LONDON")
        assert tz is not None
        assert tz.key == "Europe/London"

    def test_iana_name_resolves_directly(self):
        tz = _resolve_timezone("America/Chicago")
        assert tz is not None
        assert tz.key == "America/Chicago"

    def test_utc_alias_resolves(self):
        tz = _resolve_timezone("utc")
        assert tz is not None

    def test_gmt_alias_resolves(self):
        tz = _resolve_timezone("gmt")
        assert tz is not None

    def test_unknown_returns_none(self):
        assert _resolve_timezone("Narnia") is None

    def test_new_york_resolves(self):
        tz = _resolve_timezone("New York")
        assert tz is not None
        assert tz.key == "America/New_York"


class TestGetDatetime:
    def _fixed_now(self, tz_key="UTC"):
        """Return a fixed datetime for deterministic tests."""
        tz = ZoneInfo(tz_key)
        return datetime(2026, 4, 5, 14, 35, 0, tzinfo=tz)

    def test_local_time_returned_when_no_timezone(self):
        fixed = self._fixed_now("UTC")
        with patch("src.tools.datetime_tool.datetime") as mock_dt:
            mock_dt.now.return_value.astimezone.return_value = fixed
            result = get_datetime()
        assert "2026" in result
        assert "14:35" in result

    def test_named_city_timezone(self):
        fixed = self._fixed_now("Asia/Tokyo")
        with patch("src.tools.datetime_tool.datetime") as mock_dt:
            mock_dt.now.return_value = fixed
            result = get_datetime(timezone="Tokyo")
        assert "Asia/Tokyo" in result
        assert "2026" in result

    def test_iana_timezone_directly(self):
        fixed = self._fixed_now("America/New_York")
        with patch("src.tools.datetime_tool.datetime") as mock_dt:
            mock_dt.now.return_value = fixed
            result = get_datetime(timezone="America/New_York")
        assert "America/New_York" in result

    def test_unknown_timezone_returns_utc_fallback(self):
        fixed = self._fixed_now("UTC")
        with patch("src.tools.datetime_tool.datetime") as mock_dt:
            mock_dt.now.return_value = fixed
            result = get_datetime(timezone="Narnia")
        assert "Unknown timezone" in result
        assert "Narnia" in result
        assert "UTC" in result


class TestHandleDatetimeQuery:
    def _patch_get_datetime(
        self, return_value="Sunday 5 April 2026, 14:35 UTC"
    ):
        return patch(
            "src.tools.datetime_tool.get_datetime", return_value=return_value
        )

    def test_plain_query_calls_get_datetime_no_tz(self):
        with self._patch_get_datetime() as mock:
            _handle_datetime_query("what time is it")
        mock.assert_called_once_with()

    def test_in_location_extracted(self):
        with self._patch_get_datetime() as mock:
            _handle_datetime_query("what time is it in Tokyo")
        mock.assert_called_once_with(timezone="Tokyo")

    def test_in_location_with_question_mark(self):
        with self._patch_get_datetime() as mock:
            _handle_datetime_query("what's the time in London?")
        mock.assert_called_once_with(timezone="London")

    def test_in_location_multiword(self):
        with self._patch_get_datetime() as mock:
            _handle_datetime_query("what time is it in New York")
        mock.assert_called_once_with(timezone="New York")

    def test_in_iana_name(self):
        with self._patch_get_datetime() as mock:
            _handle_datetime_query("what time is it in America/Chicago")
        mock.assert_called_once_with(timezone="America/Chicago")

    def test_date_query_no_location(self):
        with self._patch_get_datetime() as mock:
            _handle_datetime_query("what is today's date")
        mock.assert_called_once_with()


class TestGlobalRegistration:
    def test_datetime_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "datetime" in names

    def test_datetime_tier_and_category(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "datetime")
        assert tool.router_tier == "datetime"
        assert tool.category == "time"
        assert tool.approach == "A"
