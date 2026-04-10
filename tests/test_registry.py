"""Unit tests for src/tools/registry.py."""

import pytest

from src.tools.registry import REGISTRY, ToolDefinition, ToolRegistry


def _make_tool(
    name="test_tool",
    router_tier="test_tier",
    label="Tool: test",
    description="A test tool",
    examples=None,
    default_enabled=True,
    min_tier="trivial_llm",
    approach="A",
    callable_fn=None,
    category="general",
    parameters_schema=None,
):
    return ToolDefinition(
        name=name,
        router_tier=router_tier,
        label=label,
        description=description,
        examples=examples or ["example query"],
        default_enabled=default_enabled,
        min_tier=min_tier,
        approach=approach,
        callable=callable_fn or (lambda q: f"result:{q}"),
        category=category,
        parameters_schema=parameters_schema,
    )


class TestToolDefinition:
    def test_required_fields_create_instance(self):
        tool = _make_tool()
        assert tool.name == "test_tool"
        assert tool.router_tier == "test_tier"

    def test_missing_required_field_raises_type_error(self):
        with pytest.raises(TypeError):
            ToolDefinition(name="missing_fields")  # type: ignore[call-arg]

    def test_defaults_applied(self):
        tool = _make_tool()
        assert tool.category == "general"
        assert tool.is_async is False
        assert tool.parameters_schema is None

    def test_category_can_be_set(self):
        tool = _make_tool(category="maths")
        assert tool.category == "maths"

    def test_is_async_can_be_set(self):
        tool = _make_tool()
        tool.is_async = True
        assert tool.is_async is True

    def test_parameters_schema_stored(self):
        schema = {"type": "object", "properties": {"x": {"type": "number"}}}
        tool = _make_tool(parameters_schema=schema)
        assert tool.parameters_schema == schema


class TestToolRegistryRegisterAndAll:
    def test_register_and_all(self):
        reg = ToolRegistry()
        tool = _make_tool(name="t1")
        reg.register(tool)
        assert tool in reg.all()

    def test_all_returns_list(self):
        reg = ToolRegistry()
        assert isinstance(reg.all(), list)

    def test_duplicate_name_replaces(self):
        reg = ToolRegistry()
        t1 = _make_tool(name="dup", label="First")
        t2 = _make_tool(name="dup", label="Second")
        reg.register(t1)
        reg.register(t2)
        assert len([t for t in reg.all() if t.name == "dup"]) == 1
        assert reg.all()[0].label == "Second"

    def test_multiple_tools_all_present(self):
        reg = ToolRegistry()
        reg.register(_make_tool(name="a"))
        reg.register(_make_tool(name="b"))
        names = [t.name for t in reg.all()]
        assert "a" in names and "b" in names


class TestEnabledTools:
    def test_enabled_subset_returned(self):
        reg = ToolRegistry()
        reg.register(_make_tool(name="on"))
        reg.register(_make_tool(name="off"))
        result = reg.enabled_tools({"on"})
        assert len(result) == 1
        assert result[0].name == "on"

    def test_empty_enabled_set_returns_empty(self):
        reg = ToolRegistry()
        reg.register(_make_tool(name="t"))
        assert reg.enabled_tools(set()) == []

    def test_all_enabled_returns_all(self):
        reg = ToolRegistry()
        reg.register(_make_tool(name="x"))
        reg.register(_make_tool(name="y"))
        assert len(reg.enabled_tools({"x", "y"})) == 2


class TestRouterPromptSection:
    def test_includes_enabled_tool(self):
        reg = ToolRegistry()
        reg.register(
            _make_tool(
                name="calc",
                router_tier="maths",
                description="does maths",
                examples=["2+2"],
            )
        )
        section = reg.router_prompt_section({"calc"})
        assert "maths" in section
        assert "does maths" in section
        assert "2+2" in section

    def test_excludes_disabled_tool(self):
        reg = ToolRegistry()
        reg.register(_make_tool(name="hidden", router_tier="hidden_tier"))
        section = reg.router_prompt_section(set())
        assert "hidden_tier" not in section

    def test_empty_when_no_tools(self):
        reg = ToolRegistry()
        assert reg.router_prompt_section(set()) == ""


class TestDispatch:
    def test_dispatches_to_matching_tool(self):
        reg = ToolRegistry()
        reg.register(
            _make_tool(
                name="calc",
                router_tier="maths",
                callable_fn=lambda q: "42",
            )
        )
        result = reg.dispatch("maths", "what is 6*7", {"calc"}, "trivial_llm")
        assert result == "42"

    def test_returns_none_when_no_matching_tier(self):
        reg = ToolRegistry()
        result = reg.dispatch("unknown_tier", "query", set(), "trivial_llm")
        assert result is None

    def test_returns_none_when_tool_disabled(self):
        reg = ToolRegistry()
        reg.register(_make_tool(name="t", router_tier="tier_x"))
        result = reg.dispatch("tier_x", "query", set(), "trivial_llm")
        assert result is None

    def test_min_tier_blocks_insufficient_model(self):
        reg = ToolRegistry()
        reg.register(
            _make_tool(
                name="powerful",
                router_tier="exec",
                min_tier="advanced_llm",
            )
        )
        # trivial_llm (rank 0) < advanced_llm (rank 2) → blocked
        result = reg.dispatch("exec", "query", {"powerful"}, "trivial_llm")
        assert result is None

    def test_min_tier_allows_sufficient_model(self):
        reg = ToolRegistry()
        reg.register(
            _make_tool(
                name="powerful",
                router_tier="exec",
                min_tier="advanced_llm",
                callable_fn=lambda q: "ok",
            )
        )
        result = reg.dispatch("exec", "query", {"powerful"}, "advanced_llm")
        assert result == "ok"

    def test_min_tier_allows_higher_model(self):
        reg = ToolRegistry()
        reg.register(
            _make_tool(
                name="t",
                router_tier="r",
                min_tier="simple_llm",
                callable_fn=lambda q: "result",
            )
        )
        result = reg.dispatch("r", "query", {"t"}, "complex_llm")
        assert result == "result"

    def test_tool_returning_none_propagates(self):
        reg = ToolRegistry()
        reg.register(
            _make_tool(
                name="t",
                router_tier="r",
                callable_fn=lambda q: None,
            )
        )
        result = reg.dispatch("r", "query", {"t"}, "trivial_llm")
        assert result is None

    def test_query_passed_to_callable(self):
        received = []
        reg = ToolRegistry()
        reg.register(
            _make_tool(
                name="t",
                router_tier="r",
                callable_fn=lambda q: received.append(q) or "ok",
            )
        )
        reg.dispatch("r", "my query", {"t"}, "trivial_llm")
        assert received == ["my query"]


class TestSchemas:
    def test_approach_b_tool_included(self):
        schema = {"type": "object", "properties": {"x": {"type": "number"}}}
        reg = ToolRegistry()
        reg.register(
            _make_tool(
                name="search",
                approach="B",
                parameters_schema=schema,
            )
        )
        result = reg.schemas({"search"})
        assert len(result) == 1
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "search"
        assert result[0]["function"]["strict"] is True

    def test_approach_a_tool_excluded(self):
        reg = ToolRegistry()
        reg.register(_make_tool(name="calc", approach="A"))
        assert reg.schemas({"calc"}) == []

    def test_approach_b_without_schema_excluded(self):
        reg = ToolRegistry()
        reg.register(_make_tool(name="t", approach="B", parameters_schema=None))
        assert reg.schemas({"t"}) == []

    def test_disabled_tool_excluded(self):
        schema = {"type": "object", "properties": {}}
        reg = ToolRegistry()
        reg.register(
            _make_tool(name="t", approach="B", parameters_schema=schema)
        )
        assert reg.schemas(set()) == []


class TestDispatchWithStore:
    def test_store_passed_to_tool_that_declares_it(self):
        received = {}

        def store_aware(query, store=None):
            received["store"] = store
            return "ok"

        reg = ToolRegistry()
        reg.register(
            _make_tool(name="t", router_tier="r", callable_fn=store_aware)
        )
        mock_store = object()
        result = reg.dispatch("r", "q", {"t"}, "trivial_llm", store=mock_store)
        assert result == "ok"
        assert received["store"] is mock_store

    def test_store_not_passed_to_tool_without_parameter(self):
        received = {}

        def plain(query):
            received["called"] = True
            return "plain"

        reg = ToolRegistry()
        reg.register(_make_tool(name="t", router_tier="r", callable_fn=plain))
        mock_store = object()
        result = reg.dispatch("r", "q", {"t"}, "trivial_llm", store=mock_store)
        assert result == "plain"
        assert received.get("called") is True

    def test_store_none_passed_when_memory_disabled(self):
        received = {}

        def store_aware(query, store=None):
            received["store"] = store
            return "ok"

        reg = ToolRegistry()
        reg.register(
            _make_tool(name="t", router_tier="r", callable_fn=store_aware)
        )
        reg.dispatch("r", "q", {"t"}, "trivial_llm", store=None)
        assert received["store"] is None

    def test_tool_can_call_add_on_store(self, mocker):
        mock_store = mocker.MagicMock()

        def store_aware(query, store=None):
            if store:
                store.add(text=query, source="tool_test", session_id="s1")
            return "done"

        reg = ToolRegistry()
        reg.register(
            _make_tool(name="t", router_tier="r", callable_fn=store_aware)
        )
        result = reg.dispatch(
            "r", "hello", {"t"}, "trivial_llm", store=mock_store
        )
        assert result == "done"
        mock_store.add.assert_called_once_with(
            text="hello", source="tool_test", session_id="s1"
        )


class TestGlobalRegistry:
    """The global REGISTRY has calculator and converter registered."""

    def test_calculator_registered(self):
        names = [t.name for t in REGISTRY.all()]
        assert "calculator" in names

    def test_converter_registered(self):
        names = [t.name for t in REGISTRY.all()]
        assert "converter" in names

    def test_calculator_has_correct_tier(self):
        calc = next(t for t in REGISTRY.all() if t.name == "calculator")
        assert calc.router_tier == "maths"

    def test_converter_has_correct_tier(self):
        conv = next(t for t in REGISTRY.all() if t.name == "converter")
        assert conv.router_tier == "convert"
