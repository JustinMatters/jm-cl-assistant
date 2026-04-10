"""Unit tests for Phase 27 — Session Persistence (T27.4).

Covers: save/load round-trip, list, delete, invalid names, overwrite,
missing file errors, malformed file handling.
"""

import json

import pytest

sessions_module = pytest.importorskip("src.sessions")
save_session = sessions_module.save_session
load_session = sessions_module.load_session
delete_session = sessions_module.delete_session
list_sessions = sessions_module.list_sessions
_safe_filename = sessions_module._safe_filename


# ── _safe_filename validation ────────────────────────────────────────────────


class TestSafeFilename:
    def test_valid_name_returned_stripped(self):
        assert _safe_filename("  my-session  ") == "my-session"

    def test_alphanumeric_valid(self):
        assert _safe_filename("session123") == "session123"

    def test_hyphens_valid(self):
        assert _safe_filename("my-chat-2024") == "my-chat-2024"

    def test_underscores_valid(self):
        assert _safe_filename("my_session") == "my_session"

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _safe_filename("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            _safe_filename("   ")

    def test_spaces_in_name_raises(self):
        with pytest.raises(ValueError):
            _safe_filename("my session")

    def test_special_chars_raises(self):
        with pytest.raises(ValueError):
            _safe_filename("session/../../etc")

    def test_dot_raises(self):
        with pytest.raises(ValueError):
            _safe_filename("session.json")


# ── save_session ─────────────────────────────────────────────────────────────


class TestSaveSession:
    def test_saves_json_file(self, tmp_path):
        history = [{"role": "user", "content": "hi"}]
        save_session("test", history, str(tmp_path))
        assert (tmp_path / "test.json").exists()

    def test_content_is_valid_json(self, tmp_path):
        history = [{"role": "user", "content": "hello"}]
        save_session("mysession", history, str(tmp_path))
        data = json.loads((tmp_path / "mysession.json").read_text())
        assert data == history

    def test_creates_directory_if_absent(self, tmp_path):
        subdir = tmp_path / "nested" / "sessions"
        history = [{"role": "assistant", "content": "hey"}]
        save_session("s", history, str(subdir))
        assert (subdir / "s.json").exists()

    def test_overwrites_existing_file(self, tmp_path):
        save_session("s", [{"role": "user", "content": "v1"}], str(tmp_path))
        save_session("s", [{"role": "user", "content": "v2"}], str(tmp_path))
        data = json.loads((tmp_path / "s.json").read_text())
        assert data[0]["content"] == "v2"

    def test_invalid_name_raises(self, tmp_path):
        with pytest.raises(ValueError):
            save_session("bad name!", [], str(tmp_path))

    def test_empty_history_saved(self, tmp_path):
        save_session("empty", [], str(tmp_path))
        data = json.loads((tmp_path / "empty.json").read_text())
        assert data == []


# ── load_session ─────────────────────────────────────────────────────────────


class TestLoadSession:
    def test_round_trip(self, tmp_path):
        history = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
        ]
        save_session("chat", history, str(tmp_path))
        loaded = load_session("chat", str(tmp_path))
        assert loaded == history

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_session("nonexistent", str(tmp_path))

    def test_malformed_json_value_raises_value_error(self, tmp_path):
        # Write a non-list JSON value
        (tmp_path / "bad.json").write_text('{"role": "user"}', encoding="utf-8")
        with pytest.raises(ValueError, match="malformed"):
            load_session("bad", str(tmp_path))

    def test_invalid_name_raises(self, tmp_path):
        with pytest.raises(ValueError):
            load_session("../escape", str(tmp_path))


# ── delete_session ────────────────────────────────────────────────────────────


class TestDeleteSession:
    def test_deletes_file(self, tmp_path):
        save_session("to-delete", [], str(tmp_path))
        delete_session("to-delete", str(tmp_path))
        assert not (tmp_path / "to-delete.json").exists()

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            delete_session("ghost", str(tmp_path))

    def test_invalid_name_raises(self, tmp_path):
        with pytest.raises(ValueError):
            delete_session("bad name", str(tmp_path))


# ── list_sessions ─────────────────────────────────────────────────────────────


class TestListSessions:
    def test_empty_when_directory_absent(self, tmp_path):
        missing = tmp_path / "nosuchdir"
        assert list_sessions(str(missing)) == []

    def test_returns_session_names_without_extension(self, tmp_path):
        save_session("alpha", [], str(tmp_path))
        save_session("beta", [], str(tmp_path))
        result = list_sessions(str(tmp_path))
        assert "alpha" in result
        assert "beta" in result

    def test_result_is_sorted(self, tmp_path):
        for name in ["zebra", "apple", "mango"]:
            save_session(name, [], str(tmp_path))
        result = list_sessions(str(tmp_path))
        assert result == sorted(result)

    def test_excludes_non_json_files(self, tmp_path):
        save_session("real", [], str(tmp_path))
        (tmp_path / "notes.txt").write_text("ignore me", encoding="utf-8")
        result = list_sessions(str(tmp_path))
        assert result == ["real"]

    def test_empty_directory_returns_empty_list(self, tmp_path):
        assert list_sessions(str(tmp_path)) == []
