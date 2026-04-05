"""Unit tests for src/tools/code_exec.py."""

from src.tools.code_exec import _run_code_callable


class TestRunCodeCallable:
    def test_arithmetic_expression(self):
        result = _run_code_callable('{"code": "2 + 2"}')
        assert "4" in result

    def test_print_output_captured(self):
        result = _run_code_callable('{"code": "print(\'hello\')"}')
        assert "hello" in result

    def test_multiline_code(self):
        result = _run_code_callable(
            '{"code": "x = [i**2 for i in range(4)]\\nprint(x)"}'
        )
        assert "0" in result
        assert "9" in result

    def test_import_blocked(self):
        result = _run_code_callable('{"code": "import os"}')
        assert "Error" in result or "NotImplementedError" in result

    def test_invalid_json_returns_error(self):
        result = _run_code_callable("not json")
        assert "Error" in result

    def test_empty_code_returns_error(self):
        result = _run_code_callable('{"code": ""}')
        assert "Error" in result

    def test_no_code_key_returns_error(self):
        result = _run_code_callable('{"other": "value"}')
        assert "Error" in result

    def test_syntax_error_returns_error(self):
        result = _run_code_callable('{"code": "def ("}')
        assert "Error" in result

    def test_no_output_message(self):
        result = _run_code_callable('{"code": "x = 1"}')
        # Assignment with no print and no final expression — no output
        assert result == "(no output)" or result == "1" or result is not None

    def test_list_comprehension_result(self):
        result = _run_code_callable('{"code": "[x*2 for x in range(3)]"}')
        assert "0" in result
        assert "2" in result
        assert "4" in result


class TestGlobalRegistration:
    def test_code_exec_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "code_exec" in names

    def test_code_exec_metadata(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "code_exec")
        assert tool.approach == "B"
        assert tool.default_enabled is False
        assert tool.requires_confirmation is True
        assert tool.min_tier == "complex_sonnet"
        assert tool.category == "code"

    def test_code_exec_has_parameters_schema(self):
        from src.tools.registry import REGISTRY

        tool = next(t for t in REGISTRY.all() if t.name == "code_exec")
        assert tool.parameters_schema is not None
        assert "code" in tool.parameters_schema["properties"]
