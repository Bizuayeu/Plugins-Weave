"""Configuration file loading and saving."""
from __future__ import annotations

import json
from pathlib import Path

from scripts.domain.constants import DEFAULT_SETTINGS, DEFAULT_TEXT_EXTENSIONS
from scripts.domain.exceptions import ConfigError
from scripts.domain.models import Config, Settings, Source


def load_config(config_path: str | Path) -> Config:
    """Load and validate a sources.json config file.

    Returns a Config domain object with defaults filled in.

    Raises:
        ConfigError: If config file is missing, invalid, or lacks required fields.
    """
    config_path = str(config_path)

    if not Path(config_path).exists():
        raise ConfigError(f"Config file not found: {config_path}")

    try:
        with Path(config_path).open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in {config_path}: {e}") from e

    if "sources" not in data:
        raise ConfigError(f"Missing 'sources' key in {config_path}")

    # Build Settings with defaults
    raw_settings = data.get("settings", {})
    settings = Settings(
        encoding=raw_settings.get("encoding", DEFAULT_SETTINGS["encoding"]),
        max_lines_per_file=raw_settings.get("max_lines_per_file", DEFAULT_SETTINGS["max_lines_per_file"]),
        show_summary=raw_settings.get("show_summary", DEFAULT_SETTINGS["show_summary"]),
        url_timeout=raw_settings.get("url_timeout", DEFAULT_SETTINGS["url_timeout"]),
        mode=raw_settings.get("mode", DEFAULT_SETTINGS["mode"]),
    )

    # Build text_extensions with defaults
    text_extensions = data.get("text_extensions", DEFAULT_TEXT_EXTENSIONS)

    # Build Source list
    sources = []
    for s in data["sources"]:
        sources.append(Source(
            id=s.get("id", s.get("path", "")),
            label=s.get("label", s.get("path", "")),
            path=s["path"],
            type=s.get("type", "auto"),
            enabled=s.get("enabled", True),
            description=s.get("description", ""),
            priority=s.get("priority", "normal"),
        ))

    return Config(
        version=data.get("version", "1.0.0"),
        settings=settings,
        text_extensions=text_extensions,
        sources=sources,
    )


def save_config(config_path: str | Path, config: Config) -> None:
    """Save a Config to a JSON file."""
    config_path = Path(config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "version": config.version,
        "settings": {
            "encoding": config.settings.encoding,
            "max_lines_per_file": config.settings.max_lines_per_file,
            "show_summary": config.settings.show_summary,
            "url_timeout": config.settings.url_timeout,
            "mode": config.settings.mode,
        },
        "text_extensions": config.text_extensions,
        "sources": [
            {
                "id": s.id,
                "label": s.label,
                "path": s.path,
                "type": s.type,
                "enabled": s.enabled,
                "description": s.description,
                "priority": s.priority,
            }
            for s in config.sources
        ],
    }

    with Path(config_path).open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_profile_sources(profile_path: str | Path) -> list[Source]:
    """Load sources from a profile JSON file.

    Raises:
        ConfigError: If profile file is missing or invalid.
    """
    profile_path = str(profile_path)

    if not Path(profile_path).exists():
        raise ConfigError(f"Profile not found: {profile_path}")

    try:
        with Path(profile_path).open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in profile {profile_path}: {e}") from e

    sources = []
    for s in data.get("sources", []):
        sources.append(Source(
            id=s.get("id", s.get("path", "")),
            label=s.get("label", s.get("path", "")),
            path=s["path"],
            type=s.get("type", "auto"),
            enabled=s.get("enabled", True),
            description=s.get("description", ""),
            priority=s.get("priority", "normal"),
        ))
    return sources


def list_profiles(profiles_dir: str | Path) -> list[str]:
    """List available profile names."""
    profiles_dir = Path(profiles_dir)
    if not profiles_dir.exists():
        return []
    return [
        p.stem for p in sorted(profiles_dir.glob("*.json"))
    ]
