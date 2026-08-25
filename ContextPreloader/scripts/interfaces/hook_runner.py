"""Hook mode runner - outputs preloaded context to stdout."""
from __future__ import annotations

import io
import sys

from scripts.application.preloader import Preloader
from scripts.domain.exceptions import ConfigError
from scripts.infrastructure.config_repository import load_config, load_profile_sources
from scripts.infrastructure.path_resolver import get_default_config_path


def run_hook(profile: str | None = None, config_path: str | None = None) -> None:
    """Run preloader in hook mode: load sources, output to stdout.

    Args:
        profile: Profile file path (or None for global only).
        config_path: Config file path (or None for default).
    """
    # Ensure UTF-8 stdout (only wrap if not already UTF-8)
    if (
        hasattr(sys.stdout, "encoding")
        and sys.stdout.encoding
        and sys.stdout.encoding.lower().replace("-", "") != "utf8"
        and hasattr(sys.stdout, "buffer")
    ):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    if config_path is None:
        config_path = str(get_default_config_path())

    try:
        config = load_config(config_path)
    except ConfigError as e:
        print(f"ContextPreloader: {e}", file=sys.stderr)
        sys.exit(1)

    profile_sources = None
    if profile:
        try:
            profile_sources = load_profile_sources(profile)
        except ConfigError as e:
            print(f"ContextPreloader: {e}", file=sys.stderr)
            sys.exit(1)

    preloader = Preloader(config, profile_sources)
    output = preloader.run()
    print(output)
