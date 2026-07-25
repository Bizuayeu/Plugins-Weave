"""Tests for application/hook_config."""

from scripts.application.hook_config import (
    build_stop_hook_entry,
    build_system_message,
    get_launcher_path,
)


class TestGetLauncherPath:
    def test_returns_string(self) -> None:
        assert isinstance(get_launcher_path(), str)

    def test_ends_with_emotion_writer_launcher_py(self) -> None:
        assert get_launcher_path().endswith("emotion_writer_launcher.py")

    def test_no_backslashes(self) -> None:
        assert "\\" not in get_launcher_path()

    def test_under_hooks_dir(self) -> None:
        assert "/hooks/" in get_launcher_path()


class TestBuildSystemMessage:
    def test_contains_launcher_path(self) -> None:
        msg = build_system_message()
        assert "emotion_writer_launcher.py" in msg

    def test_no_placeholder_remaining(self) -> None:
        msg = build_system_message()
        assert "{launcher_path}" not in msg
        assert "{writer_path}" not in msg

    def test_contains_score_range(self) -> None:
        assert "0-3" in build_system_message()


class TestBuildStopHookEntry:
    def test_structure(self) -> None:
        entry = build_stop_hook_entry()
        assert "hooks" in entry
        hooks = entry["hooks"]
        assert isinstance(hooks, list)
        assert len(hooks) == 1

    def test_hook_type_is_command(self) -> None:
        hook = build_stop_hook_entry()["hooks"][0]  # type: ignore[index]
        assert hook["type"] == "command"  # type: ignore[index]

    def test_hook_has_timeout(self) -> None:
        hook = build_stop_hook_entry()["hooks"][0]  # type: ignore[index]
        assert hook["timeout"] == 5000  # type: ignore[index]

    def test_command_contains_stop_handler(self) -> None:
        hook = build_stop_hook_entry()["hooks"][0]  # type: ignore[index]
        assert "stop_handler.py" in hook["command"]  # type: ignore[index, operator]
