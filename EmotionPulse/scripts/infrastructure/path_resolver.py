"""Path resolution for EmotionPulse data and config files."""

from __future__ import annotations

import os
from pathlib import Path

from scripts.domain.constants import (
    CONFIG_FILENAME,
    LOCK_FILENAME,
    PLUGIN_DATA_DIR_NAME,
    STATE_FILENAME,
)


def get_data_dir() -> Path:
    """Return ~/.claude/plugins/.emotionpulse/."""
    return Path(os.path.expanduser("~")) / ".claude" / "plugins" / PLUGIN_DATA_DIR_NAME


def get_state_file_path() -> Path:
    """Return path to emotion_state.json."""
    return get_data_dir() / STATE_FILENAME


def get_config_path() -> Path:
    """Return path to config.json."""
    return get_data_dir() / CONFIG_FILENAME


def get_lock_file_path() -> Path:
    """Return path to .hook_lock.json."""
    return get_data_dir() / LOCK_FILENAME


def get_plugin_root() -> Path | None:
    """Resolve EmotionPulse plugin root directory.

    Searches development (~/DEV/plugins-weave/EmotionPulse), marketplace
    (~/.claude/plugins/marketplaces/plugins-weave/EmotionPulse), and finally
    this module's own installation location (which is the plugin root wherever
    the tree is checked out, e.g. a CI runner) in order. Returns None if none
    has a scripts/ subdirectory.
    """
    candidates = [
        os.path.expanduser("~/DEV/plugins-weave/EmotionPulse"),
        os.path.expanduser("~/.claude/plugins/marketplaces/plugins-weave/EmotionPulse"),
        str(Path(__file__).resolve().parents[2]),
    ]
    for candidate in candidates:
        if os.path.isdir(os.path.join(candidate, "scripts")):
            return Path(candidate)
    return None
