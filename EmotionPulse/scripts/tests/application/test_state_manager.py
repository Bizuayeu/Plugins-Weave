"""Tests for application/state_manager."""

from pathlib import Path

from scripts.application.state_manager import load_state, save_state
from scripts.domain.constants import EMOTION_KEYS
from scripts.domain.models import EmotionVector


class TestStateManager:
    def test_save_load_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "state.json"
        vec = EmotionVector.from_raw_scores(
            {"calm": 2, "curiosity": 3}, session_id="s1"
        )
        save_state(vec, path=path)
        loaded = load_state(path=path)
        assert loaded is not None
        assert loaded.emotions == vec.emotions
        assert loaded.session_id == "s1"

    def test_load_missing_file(self, tmp_path: Path) -> None:
        result = load_state(path=tmp_path / "nope.json")
        assert result is None

    def test_load_corrupt_file(self, tmp_path: Path) -> None:
        path = tmp_path / "bad.json"
        path.write_text("not json!", encoding="utf-8")
        assert load_state(path=path) is None

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "sub" / "dir" / "state.json"
        vec = EmotionVector.from_raw_scores({})
        save_state(vec, path=path)
        loaded = load_state(path=path)
        assert loaded is not None

    def test_all_keys_preserved(self, tmp_path: Path) -> None:
        path = tmp_path / "state.json"
        scores = {k: i % 4 for i, k in enumerate(EMOTION_KEYS)}
        vec = EmotionVector.from_raw_scores(scores)
        save_state(vec, path=path)
        loaded = load_state(path=path)
        assert loaded is not None
        for key in EMOTION_KEYS:
            assert loaded.emotions[key] == vec.emotions[key]
