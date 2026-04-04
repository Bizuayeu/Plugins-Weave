"""Tests for domain constants."""
from scripts.domain.constants import (
    EMOTION_INDICATORS,
    EMOTION_KEYS,
    EMOTION_LABELS_EN,
    EMOTION_LABELS_JA,
    LOCK_FILENAME,
    LOCK_MAX_AGE_SECONDS,
    MAX_INTENSITY,
    MIN_INTENSITY,
    STOP_SYSTEM_MESSAGE,
)


class TestEmotionKeys:
    def test_has_seven_keys(self) -> None:
        assert len(EMOTION_KEYS) == 7

    def test_no_duplicates(self) -> None:
        assert len(EMOTION_KEYS) == len(set(EMOTION_KEYS))

    def test_order(self) -> None:
        assert EMOTION_KEYS[0] == "desperation"
        assert EMOTION_KEYS[-1] == "empathy"


class TestEmotionIndicators:
    def test_all_keys_have_indicators(self) -> None:
        for key in EMOTION_KEYS:
            assert key in EMOTION_INDICATORS


class TestEmotionLabels:
    def test_ja_covers_all(self) -> None:
        for key in EMOTION_KEYS:
            assert key in EMOTION_LABELS_JA

    def test_en_covers_all(self) -> None:
        for key in EMOTION_KEYS:
            assert key in EMOTION_LABELS_EN


class TestIntensityRange:
    def test_range(self) -> None:
        assert MIN_INTENSITY == 0
        assert MAX_INTENSITY == 3


class TestLockConstants:
    def test_lock_filename(self) -> None:
        assert LOCK_FILENAME == ".hook_lock.json"

    def test_max_age(self) -> None:
        assert LOCK_MAX_AGE_SECONDS == 60


class TestStopSystemMessage:
    def test_contains_writer_path_placeholder(self) -> None:
        assert "{writer_path}" in STOP_SYSTEM_MESSAGE

    def test_mentions_all_emotion_keys(self) -> None:
        for key in EMOTION_KEYS:
            assert key in STOP_SYSTEM_MESSAGE

    def test_mentions_score_range(self) -> None:
        assert "0-3" in STOP_SYSTEM_MESSAGE
