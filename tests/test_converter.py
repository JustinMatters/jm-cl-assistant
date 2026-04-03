"""Unit tests for src/tools/converter.py."""

from src.tools.converter import convert


class TestLength:
    def test_miles_to_km(self):
        result = convert(5, "mile", "kilometer")
        assert "8.04672" in result
        assert "km" in result

    def test_km_to_miles(self):
        result = convert(1, "kilometer", "mile")
        assert "0.621" in result

    def test_inches_to_cm(self):
        result = convert(1, "inch", "centimeter")
        assert "2.54" in result

    def test_feet_to_meters(self):
        result = convert(1, "foot", "meter")
        assert "0.3048" in result


class TestMass:
    def test_kg_to_lb(self):
        result = convert(1, "kg", "lb")
        assert "2.204" in result

    def test_lb_to_kg(self):
        result = convert(1, "lb", "kg")
        assert "0.453" in result

    def test_grams_to_oz(self):
        result = convert(100, "gram", "oz")
        assert "3.527" in result


class TestTemperature:
    def test_fahrenheit_to_celsius(self):
        result = convert(212, "degF", "degC")
        assert "100" in result

    def test_celsius_to_fahrenheit(self):
        result = convert(0, "degC", "degF")
        assert "32" in result

    def test_celsius_to_kelvin(self):
        result = convert(0, "degC", "kelvin")
        assert "273.15" in result


class TestVolume:
    def test_liters_to_gallons(self):
        result = convert(1, "liter", "gallon")
        assert "0.264" in result

    def test_ml_to_fl_oz(self):
        result = convert(100, "milliliter", "fluid_ounce")
        assert "3.38" in result


class TestSpeed:
    def test_mph_to_ms(self):
        result = convert(60, "mph", "m/s")
        assert "26.8" in result

    def test_kph_to_mph(self):
        result = convert(100, "kph", "mph")
        assert "62.1" in result


class TestTime:
    def test_hours_to_seconds(self):
        result = convert(1, "hour", "second")
        assert "3600" in result

    def test_days_to_hours(self):
        result = convert(1, "day", "hour")
        assert "24" in result

    def test_minutes_to_seconds(self):
        result = convert(2, "minute", "second")
        assert "120" in result


class TestOutputFormat:
    def test_result_contains_equals_sign(self):
        result = convert(1, "km", "mile")
        assert "=" in result

    def test_result_contains_from_value(self):
        result = convert(5, "mile", "km")
        assert "5" in result

    def test_zero_value(self):
        result = convert(0, "km", "mile")
        assert "0" in result

    def test_float_value(self):
        result = convert(1.5, "km", "mile")
        assert "=" in result
        assert "Error" not in result


class TestErrorHandling:
    def test_unknown_from_unit(self):
        result = convert(1, "blarg", "km")
        assert "Error" in result

    def test_unknown_to_unit(self):
        result = convert(1, "km", "parsec_blarg")
        assert "Error" in result

    def test_incompatible_units(self):
        result = convert(1, "kg", "meter")
        assert "Error" in result

    def test_incompatible_units_different_dimensions(self):
        result = convert(1, "second", "kilogram")
        assert "Error" in result
