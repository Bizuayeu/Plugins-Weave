"""Path resolution utilities (cross-platform)."""
from __future__ import annotations

import os
from pathlib import Path


def expand_path(path: str) -> Path:
    """Expand ~ and environment variables, normalize to absolute Path."""
    return Path(os.path.expanduser(os.path.expandvars(path))).resolve()


def get_default_config_path() -> Path:
    """Get the default sources.json path."""
    return Path.home() / ".claude" / "plugins" / ".contextpreloader" / "sources.json"


def get_profiles_dir() -> Path:
    """Get the profiles directory path."""
    return Path.home() / ".claude" / "plugins" / ".contextpreloader" / "profiles"


def get_profile_path(profile_name: str) -> Path:
    """Get the path for a named profile."""
    return get_profiles_dir() / f"{profile_name}.json"
