#!/usr/bin/env python3
"""
EpisodicRAG Infrastructure Layer
================================

外部関心事を扱う層 - ファイルI/O、ロギング、ファイルスキャン。
domain層のみに依存。

Usage:
    from infrastructure import (
        # JSON operations
        load_json,
        save_json,
        load_json_with_template,
        file_exists,
        ensure_directory,
        # File scanning
        scan_files,
        get_files_by_pattern,
        get_max_numbered_file,
        filter_files_after_number,
        count_files,
        # Logging
        get_logger,
        setup_logging,
        log_info,
        log_warning,
        log_error,
    )
"""

# JSON Repository
# File Scanner
from infrastructure.file_scanner import (
    count_files,
    filter_files_after_number,
    get_files_by_pattern,
    get_max_numbered_file,
    scan_files,
)
from infrastructure.json_repository import (
    confirm_file_overwrite,
    ensure_directory,
    file_exists,
    load_json,
    load_json_with_template,
    save_json,
    try_load_json,
    try_read_json_from_file,
)

# Logging
from infrastructure.logging_config import (
    get_logger,
    log_debug,
    log_error,
    log_info,
    log_warning,
    setup_logging,
)

# Structured Logging
from infrastructure.structured_logging import (
    StructuredLogger,
    get_structured_logger,
)

# User Interaction
from infrastructure.user_interaction import get_default_confirm_callback

# Error Handling
from infrastructure.error_handling import (
    safe_cleanup,
    safe_file_operation,
    with_error_context,
)

__all__ = [
    # JSON Repository
    "load_json",
    "save_json",
    "load_json_with_template",
    "file_exists",
    "ensure_directory",
    "try_load_json",
    "confirm_file_overwrite",
    "try_read_json_from_file",
    # File Scanner
    "scan_files",
    "get_files_by_pattern",
    "get_max_numbered_file",
    "filter_files_after_number",
    "count_files",
    # Logging
    "get_logger",
    "setup_logging",
    "log_info",
    "log_warning",
    "log_error",
    "log_debug",
    # Structured Logging
    "StructuredLogger",
    "get_structured_logger",
    # User Interaction
    "get_default_confirm_callback",
    # Error Handling
    "safe_file_operation",
    "safe_cleanup",
    "with_error_context",
]
