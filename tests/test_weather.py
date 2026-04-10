"""Unit tests for src/tools/weather.py."""

import json
from unittest.mock import MagicMock, patch

from src.tools.weather import _geocode, _handle_weather_query, get_weather


def _make_urlopen(data: dict):
    """Patch urllib.request.urlopen to return JSON data."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return patch(
        "src.tools.weather.urllib.request.urlopen", return_value=mock_resp
    )


_GEOCODE_DATA = {
    "results": [
        {
            "name": "London",
            "country": "United Kingdom",
            "latitude": 51.5074,
            "longitude": -0.1278,
        }
    ]
}

_FORECAST_DATA = {
    "daily": {
        "time": ["2026-04-05", "2026-04-06", "2026-04-07"],
        "weathercode": [1, 3, 61],
        "temperature_2m_max": [14.5, 12.0, 10.0],
        "temperature_2m_min": [8.0, 7.5, 6.0],
        "precipitation_probability_max": [10, 20, 80],
    }
}


class TestGeocode:
    def test_returns_lat_lon_and_display(self):
        with _make_urlopen(_GEOCODE_DATA):
            result = _geocode("London")
        assert result is not None
        lat, lon, display = result
        assert lat == 51.5074
        assert lon == -0.1278
        assert "London" in display

    def test_no_results_returns_none(self):
        with _make_urlopen({"results": []}):
            result = _geocode("Nowhere")
        assert result is None

    def test_missing_results_key_returns_none(self):
        with _make_urlopen({}):
            result = _geocode("X")
        assert result is None

    def test_network_error_returns_none(self):
        with patch(
            "src.tools.weather.urllib.request.urlopen",
            side_effect=OSError("timeout"),
        ):
            result = _geocode("London")
        assert result is None


class TestGetWeather:
    def _patch_geocode(self, return_value=(51.5, -0.1, "London, UK")):
        return patch("src.tools.weather._geocode", return_value=return_value)

    def test_returns_forecast_with_location_header(self):
        with self._patch_geocode(), _make_urlopen(_FORECAST_DATA):
            result = get_weather("London")
        assert "London" in result
        assert "Weather forecast" in result

    def test_includes_day_condition_temps(self):
        with self._patch_geocode(), _make_urlopen(_FORECAST_DATA):
            result = get_weather("London")
        assert "Mainly clear" in result
        assert "14°C" in result
        assert "8°C" in result

    def test_includes_precipitation(self):
        with self._patch_geocode(), _make_urlopen(_FORECAST_DATA):
            result = get_weather("London")
        assert "80% rain" in result

    def test_days_clamped_to_seven(self):
        with self._patch_geocode(), _make_urlopen(_FORECAST_DATA):
            result = get_weather("London", days=10)
        assert result  # no error

    def test_days_clamped_to_one(self):
        with self._patch_geocode(), _make_urlopen(_FORECAST_DATA):
            result = get_weather("London", days=0)
        assert result  # no error

    def test_geocode_failure_returns_error(self):
        with patch("src.tools.weather._geocode", return_value=None):
            result = get_weather("Nowhere")
        assert "Could not find location" in result

    def test_api_error_returns_error(self):
        with self._patch_geocode():
            with patch(
                "src.tools.weather.urllib.request.urlopen",
                side_effect=OSError("timeout"),
            ):
                result = get_weather("London")
        assert "Weather API error" in result

    def test_empty_daily_returns_message(self):
        with self._patch_geocode(), _make_urlopen({"daily": {}}):
            result = get_weather("London")
        assert "No forecast data" in result

    def test_auto_location_uses_ip_geolocation(self):
        mock_loc = {
            "city": "Bristol",
            "country": "United Kingdom",
            "country_code": "GB",
            "lat": 51.45,
            "lon": -2.59,
        }
        with (
            patch("src.tools.weather.get_location", return_value=mock_loc),
            _make_urlopen(_FORECAST_DATA),
        ):
            result = get_weather(location="auto")
        assert "Bristol" in result

    def test_auto_location_error_returned(self):
        with patch(
            "src.tools.weather.get_location",
            return_value={"error": "no network"},
        ):
            result = get_weather(location="auto")
        assert "Could not determine location" in result


class TestHandleWeatherQuery:
    def _patch_get_weather(self, return_value="forecast"):
        return patch("src.tools.weather.get_weather", return_value=return_value)

    def test_extracts_location_in(self):
        with self._patch_get_weather() as mock:
            _handle_weather_query("what's the weather in London")
        mock.assert_called_once_with(location="London")

    def test_extracts_location_for(self):
        with self._patch_get_weather() as mock:
            _handle_weather_query("weather forecast for Tokyo")
        mock.assert_called_once_with(location="Tokyo")

    def test_no_location_uses_auto(self):
        with self._patch_get_weather() as mock:
            _handle_weather_query("what is the weather today")
        mock.assert_called_once_with(location="auto")

    def test_location_with_question_mark(self):
        with self._patch_get_weather() as mock:
            _handle_weather_query("weather in Paris?")
        mock.assert_called_once_with(location="Paris")


class TestGlobalRegistration:
    def test_weather_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "weather" in names

    def test_weather_tier_and_category(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "weather")
        assert tool.router_tier == "weather"
        assert tool.category == "web"
        assert tool.approach == "A"
