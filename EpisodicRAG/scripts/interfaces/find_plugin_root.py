#!/usr/bin/env python3
"""
Find Plugin Root CLI
====================

EpisodicRAGプラグインルートを自動検出するCLIスクリプト。

Usage:
    python -m interfaces.find_plugin_root --output json
    python -m interfaces.find_plugin_root --output text
"""

import argparse
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional

from domain.file_constants import GRAND_DIGEST_TEMPLATE, PLUGIN_CONFIG_DIR
from interfaces.cli_helpers import output_json


@dataclass
class FindResult:
    """Plugin root search result."""

    status: str  # "ok" | "error"
    plugin_root: Optional[str] = None
    error: Optional[str] = None


def is_valid_plugin_root(path: Path) -> bool:
    """Check if path is a valid EpisodicRAG plugin root.

    Args:
        path: 検証するディレクトリパス

    Returns:
        True if valid EpisodicRAG plugin root, False otherwise
    """
    if not path.exists():
        return False
    if "EpisodicRAG" not in str(path):
        return False
    marker = path / PLUGIN_CONFIG_DIR / GRAND_DIGEST_TEMPLATE
    return marker.exists()


def _recursive_search(base_path: Path, max_depth: int, current_depth: int = 0) -> List[Path]:
    """再帰的にEpisodicRAGディレクトリを検索"""
    if current_depth > max_depth:
        return []

    results: List[Path] = []
    try:
        for item in base_path.iterdir():
            if item.is_dir():
                if item.name == "EpisodicRAG":
                    results.append(item)
                else:
                    results.extend(_recursive_search(item, max_depth, current_depth + 1))
    except (PermissionError, OSError):
        pass  # アクセス権限がない/無効なパスはスキップ

    return results


def find_in_search_paths(
    search_paths: List[Path],
    recursive: bool = False,
    max_depth: int = 5,
) -> Optional[Path]:
    """Search for EpisodicRAG plugin root in given paths.

    Args:
        search_paths: 検索するベースパスのリスト
        recursive: 再帰検索を有効にするか
        max_depth: 再帰検索の最大深度

    Returns:
        見つかった場合はプラグインルートパス、見つからない場合はNone
    """
    for base_path in search_paths:
        try:
            if not base_path.exists():
                continue
        except OSError:
            continue  # 無効なパス文字でも安全にスキップ

        # 直接チェック（EpisodicRAG サブディレクトリ）
        candidate = base_path / "EpisodicRAG"
        if is_valid_plugin_root(candidate):
            return candidate

        if recursive:
            for found in _recursive_search(base_path, max_depth):
                if is_valid_plugin_root(found):
                    return found

    return None


def get_default_search_paths() -> List[Path]:
    """Get default search paths based on platform."""
    home = Path.home()
    return [
        home / ".claude" / "plugins",
        home,
    ]


def find_plugin_root(search_paths: Optional[List[Path]] = None) -> FindResult:
    """Find EpisodicRAG plugin root.

    Args:
        search_paths: カスタム検索パス（省略時はデフォルト検索パスを使用）

    Returns:
        FindResult with status="ok" and plugin_root, or status="error" and error message
    """
    if search_paths is None:
        search_paths = get_default_search_paths()

    found = find_in_search_paths(search_paths, recursive=True)
    if found:
        return FindResult(status="ok", plugin_root=str(found))
    return FindResult(status="error", error="EpisodicRAG plugin not found")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Find EpisodicRAG plugin root")
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--search-paths",
        nargs="*",
        type=Path,
        help="Custom search paths",
    )
    args = parser.parse_args()

    search_paths = args.search_paths if args.search_paths else None
    result = find_plugin_root(search_paths=search_paths)

    if args.output == "json":
        output_json(asdict(result))
        if result.status == "error":
            sys.exit(1)
    else:
        if result.status == "ok":
            print(result.plugin_root)
        else:
            print(f"Error: {result.error}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
