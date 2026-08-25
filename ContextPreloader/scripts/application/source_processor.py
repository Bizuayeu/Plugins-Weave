"""Single source processing logic."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scripts.application.formatter import (
    format_binary_output,
    format_error_output,
    format_text_output,
    format_url_ref_output,
    format_url_text_output,
)
from scripts.domain.detection import detect_source_kind
from scripts.domain.exceptions import SourceError
from scripts.domain.models import Settings, Source
from scripts.infrastructure.file_reader import get_file_info, read_text_file
from scripts.infrastructure.url_fetcher import fetch_url


@dataclass
class ProcessedSource:
    output: str
    kind: str  # "text" | "url" | "binary" | "error"
    text_size: int  # bytes of text output (for summary)


def process_source(
    source: Source,
    settings: Settings,
    text_extensions: list[str],
) -> ProcessedSource:
    """Process a single source and return formatted output."""
    kind = detect_source_kind(source.path, text_extensions, source.type)

    try:
        if kind == "text":
            content = read_text_file(
                source.path, settings.encoding, settings.max_lines_per_file
            )
            output = format_text_output(source.label, content)
            return ProcessedSource(
                output=output, kind="text", text_size=len(content.encode("utf-8"))
            )

        elif kind == "url":
            content, content_type = fetch_url(source.path, settings.url_timeout)
            if content_type == "":
                # Error occurred
                output = format_error_output(source.label, content)
                return ProcessedSource(output=output, kind="error", text_size=0)
            elif content:
                output = format_url_text_output(source.label, source.path, content)
                return ProcessedSource(
                    output=output, kind="url", text_size=len(content.encode("utf-8"))
                )
            else:
                output = format_url_ref_output(source.label, source.path, content_type)
                return ProcessedSource(output=output, kind="binary", text_size=0)

        else:  # binary
            try:
                size, ext = get_file_info(source.path)
            except SourceError:
                size = 0
                ext = Path(source.path).suffix.lower()
            output = format_binary_output(source.label, source.path, size, ext)
            return ProcessedSource(output=output, kind="binary", text_size=0)

    except SourceError as e:
        output = format_error_output(source.label, str(e))
        return ProcessedSource(output=output, kind="error", text_size=0)
