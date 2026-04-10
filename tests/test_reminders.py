"""Unit tests for src/tools/reminders.py."""

import time

import pytest

from src.tools.reminders import (
    REMINDER_STORE,
    ReminderStore,
    _list_reminders_callable,
    _set_reminder_callable,
)


@pytest.fixture(autouse=True)
def clear_store():
    """Clear all reminders before and after each test."""
    with REMINDER_STORE._lock:
        REMINDER_STORE._reminders.clear()
    yield
    with REMINDER_STORE._lock:
        REMINDER_STORE._reminders.clear()


class TestReminderStore:
    def test_add_creates_reminder(self):
        store = ReminderStore()
        store.add("check the oven", 5, "sess1")
        assert store.count("sess1") == 1

    def test_add_returns_confirmation(self):
        store = ReminderStore()
        result = store.add("test", 3, "sess1")
        assert "3 minute" in result
        assert "test" in result

    def test_singular_minute(self):
        store = ReminderStore()
        result = store.add("test", 1, "sess1")
        assert "1 minute" in result
        assert "minutes" not in result

    def test_add_with_seconds(self):
        store = ReminderStore()
        result = store.add("test", 1.5, "sess1")
        assert "1m" in result
        assert "30s" in result

    def test_list_upcoming_empty(self):
        store = ReminderStore()
        result = store.list_upcoming("sess1")
        assert "No reminders" in result

    def test_list_upcoming_shows_reminder(self):
        store = ReminderStore()
        store.add("call back", 10, "sess1")
        result = store.list_upcoming("sess1")
        assert "call back" in result
        assert "Upcoming" in result

    def test_list_upcoming_session_isolation(self):
        store = ReminderStore()
        store.add("for sess1", 5, "sess1")
        store.add("for sess2", 5, "sess2")
        result = store.list_upcoming("sess1")
        assert "for sess1" in result
        assert "for sess2" not in result

    def test_get_due_returns_fired_reminders(self):
        store = ReminderStore()
        # Set a reminder in the past
        with store._lock:
            from src.tools.reminders import Reminder

            store._reminders.append(Reminder("past", time.time() - 1, "sess1"))
        due = store.get_due("sess1")
        assert len(due) == 1
        assert due[0].message == "past"

    def test_get_due_removes_from_store(self):
        store = ReminderStore()
        with store._lock:
            from src.tools.reminders import Reminder

            store._reminders.append(Reminder("past", time.time() - 1, "sess1"))
        store.get_due("sess1")
        assert store.count("sess1") == 0

    def test_get_due_leaves_future_reminders(self):
        store = ReminderStore()
        with store._lock:
            from src.tools.reminders import Reminder

            store._reminders.append(Reminder("past", time.time() - 1, "sess1"))
            store._reminders.append(
                Reminder("future", time.time() + 3600, "sess1")
            )
        store.get_due("sess1")
        assert store.count("sess1") == 1

    def test_get_due_session_isolation(self):
        store = ReminderStore()
        with store._lock:
            from src.tools.reminders import Reminder

            store._reminders.append(
                Reminder("for sess2", time.time() - 1, "sess2")
            )
        due = store.get_due("sess1")
        assert due == []

    def test_count_only_counts_future(self):
        store = ReminderStore()
        with store._lock:
            from src.tools.reminders import Reminder

            store._reminders.append(Reminder("past", time.time() - 1, "sess1"))
            store._reminders.append(
                Reminder("future", time.time() + 3600, "sess1")
            )
        assert store.count("sess1") == 1


class TestSetReminderCallable:
    def test_valid_args_creates_reminder(self):
        result = _set_reminder_callable(
            '{"message": "check oven", "minutes": 10}',
            session_id="s1",
        )
        assert result is not None
        assert "check oven" in result

    def test_invalid_json_returns_none(self):
        assert _set_reminder_callable("not json", session_id="s1") is None

    def test_missing_message_returns_none(self):
        assert _set_reminder_callable('{"minutes": 5}', session_id="s1") is None

    def test_zero_minutes_returns_none(self):
        assert (
            _set_reminder_callable(
                '{"message": "x", "minutes": 0}', session_id="s1"
            )
            is None
        )

    def test_negative_minutes_returns_none(self):
        assert (
            _set_reminder_callable(
                '{"message": "x", "minutes": -1}', session_id="s1"
            )
            is None
        )

    def test_default_session_id(self):
        # Should not raise even without session_id kwarg
        result = _set_reminder_callable('{"message": "x", "minutes": 1}')
        assert result is not None


class TestListRemindersCallable:
    def test_returns_no_reminders_when_empty(self):
        result = _list_reminders_callable("{}", session_id="s_empty")
        assert "No reminders" in result

    def test_shows_set_reminders(self):
        _set_reminder_callable(
            '{"message": "walk the dog", "minutes": 15}',
            session_id="s_list",
        )
        result = _list_reminders_callable("{}", session_id="s_list")
        assert "walk the dog" in result


class TestGlobalRegistration:
    def test_set_reminder_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "set_reminder" in names

    def test_list_reminders_registered(self):
        from src.tools.registry import REGISTRY

        names = [t.name for t in REGISTRY.all()]
        assert "list_reminders" in names

    def test_both_approach_b(self):
        from src.tools.registry import REGISTRY

        for name in ("set_reminder", "list_reminders"):
            tool = next(t for t in REGISTRY.all() if t.name == name)
            assert tool.approach == "B"
            assert tool.min_tier == "simple_ollama"
