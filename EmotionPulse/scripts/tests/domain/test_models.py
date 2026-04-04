"""Tests for domain models."""
import json
from datetime import datetime, timedelta, timezone

import pytest

from scripts.domain.constants import EMOTION_KEYS
from scripts.domain.models import DisplayConfig, EmotionVector, HookLock, StopHookPayload


class TestEmotionVector:
    def test_from_raw_scores_valid(self) -> None:
        scores = dict.fromkeys(EMOTION_KEYS, 2)
        vec = EmotionVector.from_raw_scores(scores, session_id="s1")
        assert vec.session_id == "s1"
        for key in EMOTION_KEYS:
            assert vec.emotions[key] == 2

    def test_clamps_high(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": 5})
        assert vec.emotions["calm"] == 3

    def test_clamps_low(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": -1})
        assert vec.emotions["calm"] == 0

    def test_missing_keys_default_zero(self) -> None:
        vec = EmotionVector.from_raw_scores({})
        for key in EMOTION_KEYS:
            assert vec.emotions[key] == 0

    def test_non_numeric_defaults_zero(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": "abc"})  # type: ignore[arg-type]
        assert vec.emotions["calm"] == 0

    def test_to_dict_roundtrip(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": 2}, session_id="s1")
        restored = EmotionVector.from_dict(vec.to_dict())
        assert restored.emotions == vec.emotions
        assert restored.session_id == "s1"

    def test_to_dict_has_version(self) -> None:
        assert EmotionVector.from_raw_scores({}).to_dict()["version"] == "1.0.0"

    def test_from_dict_invalid_emotions(self) -> None:
        vec = EmotionVector.from_dict({"emotions": "bad"})
        for key in EMOTION_KEYS:
            assert vec.emotions[key] == 0

    def test_is_frozen(self) -> None:
        with pytest.raises(AttributeError):
            EmotionVector.from_raw_scores({}).session_id = "x"  # type: ignore[misc]

    def test_all_keys_present(self) -> None:
        assert set(EmotionVector.from_raw_scores({"calm": 1}).emotions.keys()) == set(EMOTION_KEYS)


class TestStopHookPayload:
    def test_from_json(self) -> None:
        raw = json.dumps({"session_id": "s1", "reason": "done"})
        payload = StopHookPayload.from_json(raw)
        assert payload.session_id == "s1"

    def test_from_json_missing_session(self) -> None:
        payload = StopHookPayload.from_json("{}")
        assert payload.session_id == ""

    def test_from_json_invalid_raises(self) -> None:
        with pytest.raises(json.JSONDecodeError):
            StopHookPayload.from_json("bad")

    def test_is_frozen(self) -> None:
        with pytest.raises(AttributeError):
            StopHookPayload.from_json('{"session_id":"s1"}').session_id = "x"  # type: ignore[misc]


class TestHookLock:
    def test_fresh_lock(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        lock = HookLock(session_id="s1", blocked_at=now)
        assert lock.is_fresh(max_age_seconds=60) is True

    def test_expired_lock(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
        lock = HookLock(session_id="s1", blocked_at=old)
        assert lock.is_fresh(max_age_seconds=60) is False

    def test_invalid_timestamp_not_fresh(self) -> None:
        lock = HookLock(session_id="s1", blocked_at="not-a-date")
        assert lock.is_fresh() is False

    def test_empty_timestamp_not_fresh(self) -> None:
        lock = HookLock(session_id="s1", blocked_at="")
        assert lock.is_fresh() is False

    def test_to_dict_roundtrip(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        lock = HookLock(session_id="s1", blocked_at=now)
        restored = HookLock.from_dict(lock.to_dict())
        assert restored.session_id == "s1"
        assert restored.blocked_at == now

    def test_from_dict_missing_fields(self) -> None:
        lock = HookLock.from_dict({})
        assert lock.session_id == ""
        assert lock.blocked_at == ""

    def test_is_frozen(self) -> None:
        with pytest.raises(AttributeError):
            HookLock(session_id="s1", blocked_at="x").session_id = "y"  # type: ignore[misc]


class TestDisplayConfig:
    def test_defaults(self) -> None:
        cfg = DisplayConfig()
        assert cfg.show_labels is True
        assert cfg.language == "ja"

    def test_from_dict(self) -> None:
        cfg = DisplayConfig.from_dict({"show_labels": False, "language": "en"})
        assert cfg.show_labels is False
        assert cfg.language == "en"

    def test_invalid_language(self) -> None:
        assert DisplayConfig.from_dict({"language": "fr"}).language == "ja"

    def test_empty(self) -> None:
        cfg = DisplayConfig.from_dict({})
        assert cfg.show_labels is True
