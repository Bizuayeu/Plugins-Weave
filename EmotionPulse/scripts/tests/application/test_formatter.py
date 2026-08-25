"""Tests for application/formatter."""

from scripts.application.formatter import format_emotion_display
from scripts.domain.constants import EMOTION_INDICATORS
from scripts.domain.models import DisplayConfig, EmotionVector


class TestFormatEmotionDisplay:
    def test_labels_off(self) -> None:
        vec = EmotionVector.from_raw_scores(
            {"calm": 2, "curiosity": 3, "playfulness": 1}
        )
        config = DisplayConfig(show_labels=False)
        result = format_emotion_display(vec, config)
        expected = (
            f"{EMOTION_INDICATORS['calm'] * 2}, "
            f"{EMOTION_INDICATORS['curiosity'] * 3}, "
            f"{EMOTION_INDICATORS['playfulness'] * 1}"
        )
        assert result == expected

    def test_labels_on_ja(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": 2, "curiosity": 3})
        config = DisplayConfig(show_labels=True, language="ja")
        result = format_emotion_display(vec, config)
        assert "落ち着き:" in result
        assert "知的興奮:" in result

    def test_labels_on_en(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": 2, "curiosity": 3})
        config = DisplayConfig(show_labels=True, language="en")
        result = format_emotion_display(vec, config)
        assert "calm:" in result
        assert "curiosity:" in result

    def test_all_zeros_produces_empty(self) -> None:
        vec = EmotionVector.from_raw_scores({})
        result = format_emotion_display(vec)
        assert result == ""

    def test_omits_zero_values(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": 0, "curiosity": 2})
        config = DisplayConfig(show_labels=True, language="ja")
        result = format_emotion_display(vec, config)
        assert "落ち着き" not in result
        assert "知的興奮" in result

    def test_max_intensity(self) -> None:
        vec = EmotionVector.from_raw_scores({"desperation": 3})
        config = DisplayConfig(show_labels=False)
        result = format_emotion_display(vec, config)
        assert result == EMOTION_INDICATORS["desperation"] * 3

    def test_single_emotion(self) -> None:
        vec = EmotionVector.from_raw_scores({"empathy": 1})
        config = DisplayConfig(show_labels=True, language="ja")
        result = format_emotion_display(vec, config)
        assert result == f"対人配慮:{EMOTION_INDICATORS['empathy']}"
        assert ", " not in result

    def test_respects_key_order(self) -> None:
        vec = EmotionVector.from_raw_scores({"empathy": 1, "desperation": 1})
        config = DisplayConfig(show_labels=True, language="en")
        result = format_emotion_display(vec, config)
        desp_pos = result.index("desperation")
        emp_pos = result.index("empathy")
        assert desp_pos < emp_pos

    def test_default_config_is_ja_with_labels(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": 1})
        result = format_emotion_display(vec)
        assert "落ち着き:" in result

    def test_comma_separator(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": 1, "curiosity": 1})
        config = DisplayConfig(show_labels=False)
        result = format_emotion_display(vec, config)
        assert ", " in result
