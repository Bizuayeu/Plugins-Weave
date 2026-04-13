"""Output formatting functions."""
from __future__ import annotations

from scripts.domain.detection import format_file_size, get_file_type_label


def format_text_output(label: str, content: str) -> str:
    return f"=== {label} ===\n{content}\n"


def format_binary_output(label: str, path: str, size: int, ext: str) -> str:
    type_label = get_file_type_label(ext)
    size_str = format_file_size(size)
    return (
        f"=== {label} [{type_label}] ===\n"
        f"Path: {path}\n"
        f"Type: {type_label}\n"
        f"Size: {size_str}\n"
        f"Note: Use Read tool to view this file\n"
    )


def format_url_text_output(label: str, url: str, content: str) -> str:
    return (
        f"=== {label} [URL] ===\n"
        f"Source: {url}\n"
        f"{content}\n"
    )


def format_url_ref_output(label: str, url: str, content_type: str) -> str:
    return (
        f"=== {label} [URL] ===\n"
        f"Source: {url}\n"
        f"Content-Type: {content_type}\n"
        f"Note: Use WebFetch tool to view this content\n"
    )


def format_error_output(label: str, error: str) -> str:
    return (
        f"=== {label} [ERROR] ===\n"
        f"{error}\n"
    )


def format_reference_output(
    sources: list[tuple[str, str, str, str]],
) -> str:
    """Reference mode output: compact instruction with paths and descriptions.

    Args:
        sources: list of (path, label, description, priority) tuples.
    """
    lines = [
        "=== ContextPreloader: Session Context ===",
        "Read the following files using the Read tool before responding to the user.",
        "",
    ]
    for i, (path, label, description, priority) in enumerate(sources, 1):
        tag = f"[{priority.upper()}]"
        lines.append(f"{i}. {tag} {label}")
        lines.append(f"   Path: {path}")
        if description:
            lines.append(f"   {description}")
        lines.append("")
    return "\n".join(lines)


def format_summary(
    text_count: int, url_count: int, binary_count: int, total_kb: float
) -> str:
    parts = []
    if text_count:
        parts.append(f"{text_count} text file{'s' if text_count != 1 else ''}")
    if url_count:
        parts.append(f"{url_count} URL{'s' if url_count != 1 else ''}")
    if binary_count:
        parts.append(f"{binary_count} binary reference{'s' if binary_count != 1 else ''}")

    loaded = ", ".join(parts) if parts else "nothing"
    return (
        f"=== ContextPreloader Summary ===\n"
        f"Loaded: {loaded}\n"
        f"Total text: ~{total_kb:.0f}KB\n"
    )
