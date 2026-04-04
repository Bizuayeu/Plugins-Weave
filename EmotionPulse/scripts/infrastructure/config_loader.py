"""Load plugin display configuration from config.json."""
from __future__ import annotations

from scripts.domain.models import DisplayConfig
from scripts.infrastructure.file_io import read_json_safe
from scripts.infrastructure.path_resolver import get_config_path


def load_display_config() -> DisplayConfig:
    """Load display config, returning defaults on any failure."""
    data = read_json_safe(get_config_path())
    if data is None:
        return DisplayConfig()
    display_section = data.get("display", {})
    if not isinstance(display_section, dict):
        return DisplayConfig()
    return DisplayConfig.from_dict(display_section)
