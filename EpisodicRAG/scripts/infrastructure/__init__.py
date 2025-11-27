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
from infrastructure.json_repository import (
    load_json,
    save_json,
    load_json_with_template,
    file_exists,
    ensure_directory,
)

# File Scanner
from infrastructure.file_scanner import (
    scan_files,
    get_files_by_pattern,
    get_max_numbered_file,
    filter_files_after_number,
    count_files,
)

# Logging
from infrastructure.logging_config import (
    get_logger,
    setup_logging,
    log_info,
    log_warning,
    log_error,
)

__all__ = [
    # JSON Repository
    "load_json",
    "save_json",
    "load_json_with_template",
    "file_exists",
    "ensure_directory",
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
]
