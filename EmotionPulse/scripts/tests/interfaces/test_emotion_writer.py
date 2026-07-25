"""Tests for interfaces/emotion_writer."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.interfaces.emotion_writer import main


class TestEmotionWriterMain:
    def test_writes_valid_json(self) -> None:
        scores = {"calm": 2, "curiosity": 3}
        with (
            patch("sys.argv", ["emotion_writer.py", json.dumps(scores)]),
            patch(
                "scripts.interfaces.emotion_writer.save_state",
            ) as mock_save,
        ):
            main()
        mock_save.assert_called_once()
        vec = mock_save.call_args[0][0]
        assert vec.emotions["calm"] == 2
        assert vec.emotions["curiosity"] == 3

    def test_clamps_values(self) -> None:
        scores = {"calm": 5, "curiosity": -1}
        with (
            patch("sys.argv", ["emotion_writer.py", json.dumps(scores)]),
            patch("scripts.interfaces.emotion_writer.save_state") as mock_save,
        ):
            main()
        vec = mock_save.call_args[0][0]
        assert vec.emotions["calm"] == 3
        assert vec.emotions["curiosity"] == 0

    def test_no_args_exits(self) -> None:
        with (
            patch("sys.argv", ["emotion_writer.py"]),
            pytest.raises(SystemExit, match="1"),
        ):
            main()

    def test_invalid_json_exits(self) -> None:
        with (
            patch("sys.argv", ["emotion_writer.py", "not json"]),
            pytest.raises(SystemExit, match="1"),
        ):
            main()

    def test_non_dict_exits(self) -> None:
        with (
            patch("sys.argv", ["emotion_writer.py", "[1,2,3]"]),
            pytest.raises(SystemExit, match="1"),
        ):
            main()

    def test_all_keys_present(self) -> None:
        from scripts.domain.constants import EMOTION_KEYS

        scores = {"calm": 1}
        with (
            patch("sys.argv", ["emotion_writer.py", json.dumps(scores)]),
            patch("scripts.interfaces.emotion_writer.save_state") as mock_save,
        ):
            main()
        vec = mock_save.call_args[0][0]
        assert set(vec.emotions.keys()) == set(EMOTION_KEYS)
