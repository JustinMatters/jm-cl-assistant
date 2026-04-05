"""Session-scoped reminder / timer tool.

Stores reminders in a thread-safe module-level store keyed by session ID.
The Gradio UI polls ``REMINDER_STORE.get_due()`` every 10 seconds via
``gr.Timer`` and injects any fired reminders into the chat history.

Two Approach B tools are registered:
- ``set_reminder`` — schedule a reminder N minutes from now
- ``list_reminders`` — list upcoming reminders for this session
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass


@dataclass
class Reminder:
    """A single scheduled reminder.

    Attributes:
        message: The reminder text to display when it fires.
        due_at: Unix timestamp when the reminder should fire.
        session_id: Identifier of the session that created it.
    """

    message: str
    due_at: float
    session_id: str


class ReminderStore:
    """Thread-safe, session-scoped reminder storage.

    Reminders are stored in memory for the lifetime of the process.
    All public methods are safe to call from multiple threads
    (e.g. the Gradio event thread and the timer polling thread).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._reminders: list[Reminder] = []

    def add(self, message: str, minutes: float, session_id: str) -> str:
        """Schedule a reminder.

        Args:
            message: Text to show when the reminder fires.
            minutes: Delay in minutes from now.
            session_id: Session that owns this reminder.

        Returns:
            A human-readable confirmation string.
        """
        due_at = time.time() + minutes * 60
        reminder = Reminder(
            message=message, due_at=due_at, session_id=session_id
        )
        with self._lock:
            self._reminders.append(reminder)
        logging.debug(
            "Reminder set for session %s in %.1f min: %r",
            session_id,
            minutes,
            message,
        )
        mins = int(minutes)
        secs = int((minutes - mins) * 60)
        if secs:
            return f"Reminder set for {mins}m {secs}s: {message}"
        plural = "s" if mins != 1 else ""
        return f"Reminder set for {mins} minute{plural}: {message}"

    def list_upcoming(self, session_id: str) -> str:
        """Return a formatted list of upcoming reminders for a session.

        Args:
            session_id: The session to query.

        Returns:
            A human-readable list, or a message if there are none.
        """
        now = time.time()
        with self._lock:
            upcoming = [
                r
                for r in self._reminders
                if r.session_id == session_id and r.due_at > now
            ]
        if not upcoming:
            return "No reminders set."
        lines = ["Upcoming reminders:"]
        for r in sorted(upcoming, key=lambda x: x.due_at):
            remaining = r.due_at - now
            mins = int(remaining // 60)
            secs = int(remaining % 60)
            lines.append(f"  • {r.message} (in {mins}m {secs}s)")
        return "\n".join(lines)

    def get_due(self, session_id: str) -> list[Reminder]:
        """Return and remove reminders that are due for a session.

        Args:
            session_id: The session to check.

        Returns:
            List of ``Reminder`` objects that are now due.
        """
        now = time.time()
        due: list[Reminder] = []
        with self._lock:
            remaining: list[Reminder] = []
            for r in self._reminders:
                if r.session_id == session_id and r.due_at <= now:
                    due.append(r)
                else:
                    remaining.append(r)
            self._reminders = remaining
        return due

    def count(self, session_id: str) -> int:
        """Return the number of pending reminders for a session.

        Args:
            session_id: The session to count for.

        Returns:
            Number of upcoming reminders.
        """
        now = time.time()
        with self._lock:
            return sum(
                1
                for r in self._reminders
                if r.session_id == session_id and r.due_at > now
            )


#: Global singleton used by all sessions.
REMINDER_STORE = ReminderStore()


# ── Tool registration ────────────────────────────────────────────────────────

from src.tools.registry import REGISTRY, ToolDefinition  # noqa: E402


def _set_reminder_callable(args_json: str, session_id: str = "") -> str | None:
    """Approach B callable for set_reminder.

    Args:
        args_json: JSON string with ``message`` and ``minutes`` keys.
        session_id: Injected by the orchestrator's B executor.

    Returns:
        Confirmation string, or ``None`` if arguments are invalid.
    """
    try:
        args = json.loads(args_json)
        message = str(args.get("message", "")).strip()
        minutes = float(args.get("minutes", 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    if not message or minutes <= 0:
        return None

    return REMINDER_STORE.add(message, minutes, session_id)


def _list_reminders_callable(args_json: str, session_id: str = "") -> str:
    """Approach B callable for list_reminders.

    Args:
        args_json: JSON string (ignored — no parameters needed).
        session_id: Injected by the orchestrator's B executor.

    Returns:
        A formatted list of upcoming reminders.
    """
    return REMINDER_STORE.list_upcoming(session_id)


REGISTRY.register(
    ToolDefinition(
        name="set_reminder",
        router_tier="set_reminder",
        label="Tool: set reminder",
        description=(
            "set a reminder that fires after a specified number of minutes"
        ),
        examples=[
            "remind me in 10 minutes to check the oven",
            "set a reminder for 5 minutes",
            "remind me to call back in 30 minutes",
        ],
        default_enabled=True,
        min_tier="simple_ollama",
        approach="B",
        callable=_set_reminder_callable,
        category="time",
        parameters_schema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "What to remind the user about",
                },
                "minutes": {
                    "type": "number",
                    "description": "How many minutes until the reminder fires",
                },
            },
            "required": ["message", "minutes"],
            "additionalProperties": False,
        },
    )
)

REGISTRY.register(
    ToolDefinition(
        name="list_reminders",
        router_tier="list_reminders",
        label="Tool: list reminders",
        description="show all upcoming reminders for this session",
        examples=[
            "what reminders do I have",
            "list my reminders",
            "show reminders",
        ],
        default_enabled=True,
        min_tier="simple_ollama",
        approach="B",
        callable=_list_reminders_callable,
        category="time",
        parameters_schema={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    )
)
