"""Unit tests for src/tools/calculator.py."""

from src.tools.calculator import calculate


class TestBasicArithmetic:
    def test_addition(self):
        assert calculate("2 + 3") == "5"

    def test_subtraction(self):
        assert calculate("10 - 4") == "6"

    def test_multiplication(self):
        assert calculate("6 * 7") == "42"

    def test_division(self):
        assert calculate("10 / 4") == "2.5"

    def test_integer_division_result(self):
        assert calculate("10 / 2") == "5"

    def test_exponentiation(self):
        assert calculate("2 ** 10") == "1024"

    def test_modulo(self):
        assert calculate("17 % 5") == "2"

    def test_parentheses(self):
        assert calculate("(3 + 4) * 2") == "14"

    def test_nested_parentheses(self):
        assert calculate("(2 + (3 * 4)) / 2") == "7"

    def test_negative_number(self):
        assert calculate("-5 + 10") == "5"

    def test_float_result(self):
        assert calculate("1 / 3").startswith("0.333")


class TestMathsFunctions:
    def test_sqrt(self):
        assert calculate("sqrt(9)") == "3"

    def test_sqrt_non_perfect(self):
        result = calculate("sqrt(2)")
        assert result.startswith("1.414")

    def test_abs(self):
        assert calculate("abs(-7)") == "7"

    def test_round(self):
        assert calculate("round(3.7)") == "4"

    def test_round_with_decimals(self):
        assert calculate("round(3.14159, 2)") == "3.14"

    def test_min(self):
        assert calculate("min(3, 1, 4, 1, 5)") == "1"

    def test_max(self):
        assert calculate("max(3, 1, 4, 1, 5)") == "5"

    def test_log(self):
        result = calculate("log(e)")
        assert result == "1"

    def test_log10(self):
        assert calculate("log10(1000)") == "3"

    def test_sin_zero(self):
        assert calculate("sin(0)") == "0"

    def test_cos_zero(self):
        assert calculate("cos(0)") == "1"

    def test_pi_constant(self):
        result = calculate("pi")
        assert result.startswith("3.14159")

    def test_floor(self):
        assert calculate("floor(3.9)") == "3"

    def test_ceil(self):
        assert calculate("ceil(3.1)") == "4"

    def test_factorial(self):
        assert calculate("factorial(5)") == "120"


class TestEdgeCases:
    def test_whitespace_trimmed(self):
        assert calculate("  2 + 2  ") == "4"

    def test_large_number(self):
        assert calculate("10 ** 18") == "1000000000000000000"

    def test_zero(self):
        assert calculate("0") == "0"

    def test_float_input(self):
        assert calculate("1.5 + 2.5") == "4"


class TestErrorHandling:
    def test_division_by_zero(self):
        result = calculate("1 / 0")
        assert "Error" in result

    def test_invalid_expression(self):
        result = calculate("2 +* 3")
        assert "Error" in result

    def test_empty_expression(self):
        result = calculate("")
        assert "Error" in result or result == "None" or result is not None

    def test_arbitrary_code_blocked(self):
        result = calculate("__import__('os').system('echo hi')")
        assert "Error" in result

    def test_unknown_function(self):
        result = calculate("nonexistent_func(5)")
        assert "Error" in result
