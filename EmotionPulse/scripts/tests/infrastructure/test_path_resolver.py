"""Tests for infrastructure/path_resolver."""
from pathlib import Path

from scripts.infrastructure.path_resolver import (
    get_config_path,
    get_data_dir,
    get_lock_file_path,
    get_state_file_path,
)


class TestPathResolver:
    def test_data_dir_ends_with_emotionpulse(self) -> None:
        path = get_data_dir()
        assert path.name == ".emotionpulse"
        assert path.parent.name == "plugins"

    def test_state_file_path(self) -> None:
        path = get_state_file_path()
        assert path.name == "emotion_state.json"
        assert path.parent == get_data_dir()

    def test_config_path(self) -> None:
        path = get_config_path()
        assert path.name == "config.json"
        assert path.parent == get_data_dir()

    def test_lock_file_path(self) -> None:
        path = get_lock_file_path()
        assert path.name == ".hook_lock.json"
        assert path.parent == get_data_dir()

    def test_paths_are_absolute(self) -> None:
        assert get_data_dir().is_absolute()
        assert get_state_file_path().is_absolute()
        assert get_config_path().is_absolute()
        assert get_lock_file_path().is_absolute()
