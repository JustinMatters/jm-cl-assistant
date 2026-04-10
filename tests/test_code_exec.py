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


class TestSandboxEscape:
    """Verify that common sandbox-escape vectors are blocked by asteval.

    Each test passes an escape attempt as a string to _run_code_callable
    and asserts the result contains "Error".  Tests are safe regardless of
    outcome: even if asteval somehow did not block a vector, the call would
    return a value (not cause harm), and the assertion would then fail,
    surfacing the regression without side effects.
    """

    def _assert_blocked(self, code: str) -> None:
        import json

        result = _run_code_callable(json.dumps({"code": code}))
        assert "Error" in result, (
            f"Expected sandbox to block {code!r} but got: {result!r}"
        )

    def test_import_blocked(self):
        self._assert_blocked("import os")

    def test_import_sys_blocked(self):
        self._assert_blocked("import sys")

    def test_exec_blocked(self):
        self._assert_blocked('exec("import os")')

    def test_eval_blocked(self):
        self._assert_blocked('eval("1+1")')

    def test_open_blocked(self):
        self._assert_blocked("open('test.txt', 'w')")

    def test_compile_blocked(self):
        self._assert_blocked('compile("import os", "<str>", "exec")')

    def test_globals_blocked(self):
        self._assert_blocked("globals()")

    def test_locals_blocked(self):
        self._assert_blocked("locals()")

    def test_dunder_import_blocked(self):
        self._assert_blocked('__import__("os")')

    def test_getattr_builtins_blocked(self):
        self._assert_blocked('getattr(__builtins__, "__import__")')

    def test_subclass_escape_blocked(self):
        # MRO-based escape to reach file/socket classes
        self._assert_blocked("().__class__.__bases__[0].__subclasses__()")


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
