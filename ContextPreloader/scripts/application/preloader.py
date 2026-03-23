"""Preloader: orchestrates source processing."""
from __future__ import annotations

from scripts.domain.models import Config, Source
from scripts.application.formatter import format_summary
from scripts.application.profile_merger import merge_sources
from scripts.application.source_processor import process_source


class Preloader:
    """Main preloader that processes all sources and produces output."""

    def __init__(
        self,
        config: Config,
        profile_sources: list[Source] | None = None,
    ):
        self._config = config
        self._profile_sources = profile_sources

    def run(self) -> str:
        """Process all sources and return combined output string."""
        all_sources = merge_sources(self._config.sources, self._profile_sources)

        parts: list[str] = []
        text_count = 0
        url_count = 0
        binary_count = 0
        total_text_bytes = 0

        for source in all_sources:
            if not source.enabled:
                continue

            result = process_source(
                source, self._config.settings, self._config.text_extensions
            )
            parts.append(result.output)
            total_text_bytes += result.text_size

            if result.kind == "text":
                text_count += 1
            elif result.kind == "url":
                url_count += 1
            elif result.kind == "binary":
                binary_count += 1
            elif result.kind == "error":
                text_count += 0  # errors don't count

        if self._config.settings.show_summary:
            total_kb = total_text_bytes / 1024
            parts.append(format_summary(text_count, url_count, binary_count, total_kb))

        return "\n".join(parts)
