"""Tests for infrastructure/path_resolver."""

from pathlib import Path
from unittest.mock import patch

from scripts.infrastructure import path_resolver
from scripts.infrastructure.path_resolver import (
    get_config_path,
    get_data_dir,
    get_lock_file_path,
    get_plugin_root,
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


class TestGetPluginRoot:
    """~/DEV/... か ~/.claude/plugins/marketplaces/... を優先順で探索する."""

    def test_returns_dev_candidate_when_exists(self) -> None:
        """DEV 候補の scripts/ が存在 → DEV 候補を返す."""
        with patch.object(Path, "is_dir", lambda self: "DEV" in str(self)):
            root = get_plugin_root()
        assert root is not None
        assert "DEV" in str(root)
        assert root.name == "EmotionPulse"

    def test_returns_marketplace_candidate_when_dev_missing(self) -> None:
        """DEV 候補なし、marketplace 候補あり → marketplace 返す."""
        with patch.object(Path, "is_dir", lambda self: "marketplaces" in str(self)):
            root = get_plugin_root()
        assert root is not None
        assert "marketplaces" in str(root)
        assert root.name == "EmotionPulse"

    def test_returns_installed_location_when_named_candidates_missing(self) -> None:
        """DEV / marketplace のどちらも無い（CI 等）→ 自身の設置場所を返す."""
        expected = Path(path_resolver.__file__).resolve().parents[2]
        with patch.object(
            Path, "is_dir", lambda self: str(self).startswith(str(expected))
        ):
            root = get_plugin_root()
        assert root == expected

    def test_returns_none_when_all_missing(self) -> None:
        """どの候補にも scripts/ が無い → None."""
        with patch.object(Path, "is_dir", lambda self: False):
            root = get_plugin_root()
        assert root is None
