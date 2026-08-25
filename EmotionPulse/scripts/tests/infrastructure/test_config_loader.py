"""Tests for infrastructure/config_loader."""

from unittest.mock import patch

from scripts.domain.models import DisplayConfig
from scripts.infrastructure.config_loader import load_display_config


class TestLoadDisplayConfig:
    def test_returns_defaults_when_no_file(self) -> None:
        with patch(
            "scripts.infrastructure.config_loader.read_json_safe", return_value=None
        ):
            cfg = load_display_config()
        assert cfg.show_labels is True
        assert cfg.language == "ja"

    def test_reads_display_section(self) -> None:
        data: dict[str, object] = {"display": {"show_labels": False, "language": "en"}}
        with patch(
            "scripts.infrastructure.config_loader.read_json_safe", return_value=data
        ):
            cfg = load_display_config()
        assert cfg.show_labels is False
        assert cfg.language == "en"

    def test_invalid_display_section(self) -> None:
        data: dict[str, object] = {"display": "bad"}
        with patch(
            "scripts.infrastructure.config_loader.read_json_safe", return_value=data
        ):
            cfg = load_display_config()
        assert isinstance(cfg, DisplayConfig)
        assert cfg.show_labels is True
