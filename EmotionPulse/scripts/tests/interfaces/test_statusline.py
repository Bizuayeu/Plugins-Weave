"""Tests for interfaces/statusline."""

from unittest.mock import patch

from scripts.domain.models import DisplayConfig, EmotionVector
from scripts.interfaces.statusline import run_statusline


class TestRunStatusline:
    def test_outputs_emoji(self) -> None:
        vec = EmotionVector.from_raw_scores({"calm": 2, "curiosity": 1})
        config = DisplayConfig(show_labels=False)
        with (
            patch("scripts.interfaces.statusline.load_state", return_value=vec),
            patch(
                "scripts.interfaces.statusline.load_display_config", return_value=config
            ),
        ):
            run_statusline()
        # Verify no crash; actual output tested in formatter tests

    def test_no_state_file_outputs_nothing(self) -> None:
        with patch("scripts.interfaces.statusline.load_state", return_value=None):
            run_statusline()  # Should not raise

    def test_exception_does_not_crash(self) -> None:
        with patch(
            "scripts.interfaces.statusline.load_state",
            side_effect=Exception("unexpected"),
        ):
            run_statusline()  # Should not raise

    def test_all_zeros_outputs_nothing(self) -> None:
        vec = EmotionVector.from_raw_scores({})
        config = DisplayConfig(show_labels=False)
        with (
            patch("scripts.interfaces.statusline.load_state", return_value=vec),
            patch(
                "scripts.interfaces.statusline.load_display_config", return_value=config
            ),
        ):
            run_statusline()  # Empty output, no crash
