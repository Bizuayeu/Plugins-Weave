"""Domain models for ContextPreloader."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    """A single context source (file path or URL)."""

    id: str
    label: str
    path: str
    type: str = "auto"
    enabled: bool = True
    description: str = ""
    priority: str = "normal"


@dataclass(frozen=True)
class Settings:
    """Global preloader settings."""

    encoding: str = "utf-8"
    max_lines_per_file: int = 0
    show_summary: bool = True
    url_timeout: int = 10
    mode: str = "inline"


@dataclass(frozen=True)
class Config:
    """Complete preloader configuration."""

    version: str
    settings: Settings
    text_extensions: list[str]
    sources: list[Source]
