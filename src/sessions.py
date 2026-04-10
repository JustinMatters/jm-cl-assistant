"""Session persistence for jm-cl-assistant.

Saves and loads named conversation sessions as JSON files in a ``sessions/``
directory, complementing the RAG memory store with verbatim history replay.
"""

import json
import re
from pathlib import Path

_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


def _safe_filename(name: str) -> str:
    """Validate and return the sanitised session name.

    Args:
        name: User-provided session name (will be stripped).

    Returns:
        The stripped name if valid.

    Raises:
        ValueError: If the name is empty or contains characters other than
          alphanumeric, hyphens, or underscores.
    """
    name = name.strip()
    if not name:
        raise ValueError("Session name must not be empty")
    if not _SAFE_NAME_RE.match(name):
        raise ValueError(
            "Session name may only contain letters, digits, "
            "hyphens, and underscores"
        )
    return name


def save_session(
    name: str,
    history: list[dict],
    path: str = "sessions/",
) -> None:
    """Save a conversation history to a named session file.

    Creates the sessions directory if it does not exist.  Overwrites an
    existing file of the same name without warning — callers are
    responsible for any overwrite guard logic.

    Args:
        name: Session name (alphanumeric, hyphens, underscores only).
        history: Conversation history as a list of message dicts.
        path: Directory where session files are stored.

    Raises:
        ValueError: If ``name`` contains invalid characters or is empty.
    """
    safe = _safe_filename(name)
    sessions_dir = Path(path)
    sessions_dir.mkdir(parents=True, exist_ok=True)
    file = sessions_dir / f"{safe}.json"
    file.write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_session(
    name: str,
    path: str = "sessions/",
) -> list[dict]:
    """Load a named session from disk.

    Args:
        name: Session name.
        path: Directory where session files are stored.

    Returns:
        The conversation history as a list of message dicts.

    Raises:
        ValueError: If ``name`` is invalid or the file content is malformed.
        FileNotFoundError: If the session file does not exist.
    """
    safe = _safe_filename(name)
    file = Path(path) / f"{safe}.json"
    if not file.exists():
        raise FileNotFoundError(f"Session {name!r} not found")
    data = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Session file for {name!r} is malformed")
    return data


def delete_session(name: str, path: str = "sessions/") -> None:
    """Delete a named session file.

    Args:
        name: Session name.
        path: Directory where session files are stored.

    Raises:
        ValueError: If ``name`` is invalid.
        FileNotFoundError: If the session file does not exist.
    """
    safe = _safe_filename(name)
    file = Path(path) / f"{safe}.json"
    if not file.exists():
        raise FileNotFoundError(f"Session {name!r} not found")
    file.unlink()


def list_sessions(path: str = "sessions/") -> list[str]:
    """Return a sorted list of saved session names.

    Args:
        path: Directory where session files are stored.

    Returns:
        Sorted list of session names (without the ``.json`` extension).
        Returns an empty list if the directory does not exist.
    """
    sessions_dir = Path(path)
    if not sessions_dir.exists():
        return []
    return sorted(f.stem for f in sessions_dir.glob("*.json"))
