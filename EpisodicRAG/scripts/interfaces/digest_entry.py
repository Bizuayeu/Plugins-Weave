#!/usr/bin/env python3
"""
Digest Entry Point CLI
======================

/digest コマンドのPythonエントリポイント。

Pattern 1 (引数なし): 新Loop検出
Pattern 2 (level指定): 階層確定準備

Usage:
    python -m interfaces.digest_entry           # Pattern 1
    python -m interfaces.digest_entry weekly    # Pattern 2
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from domain.constants import DIGEST_LEVEL_NAMES
from domain.file_constants import CONFIG_FILENAME
from infrastructure.config import get_persistent_config_dir
from infrastructure.json_repository import load_json


@dataclass
class DigestEntryResult:
    """/digest コマンド実行結果"""

    status: str  # "ok" | "error"
    pattern: int  # 1 or 2
    base_dir: str | None = None
    loops_path: str | None = None
    digests_path: str | None = None
    essences_path: str | None = None

    # Pattern 1 専用
    new_loops: list[str] = field(default_factory=list)
    new_loops_count: int = 0

    # Pattern 2 専用
    level: str | None = None
    shadow_state: dict[str, Any] | None = None

    # 共通
    weekly_source_count: int = 0
    weekly_threshold: int = 5
    message: str = ""
    error: str | None = None


def get_paths_from_config() -> dict[str, Any]:
    """config.json からパス情報を取得"""
    config_file = get_persistent_config_dir() / CONFIG_FILENAME
    config = load_json(config_file)

    base_dir_str = config.get("base_dir", "")
    if not base_dir_str:
        raise ValueError("base_dir is required in config.json")

    base_path = Path(base_dir_str).expanduser().resolve()

    paths = config.get("paths", {})
    levels = config.get("levels", {})

    return {
        "base_dir": base_path,
        "loops_path": base_path / paths.get("loops_dir", "data/Loops"),
        "digests_path": base_path / paths.get("digests_dir", "data/Digests"),
        "essences_path": base_path / paths.get("essences_dir", "data/Essences"),
        "weekly_threshold": levels.get("weekly_threshold", 5),
    }


def get_new_loops() -> list[str]:
    """新規Loopファイルを検出（ShadowUpdaterと同じロジック）"""
    from application.config import DigestConfig
    from application.grand import ShadowGrandDigestManager

    config = DigestConfig()
    manager = ShadowGrandDigestManager(config)

    # FileDetectorを使って新規ファイルを検出
    new_files = manager._detector.find_new_files("weekly")
    return [f.stem for f in new_files]


def get_weekly_source_count() -> int:
    """weekly Shadowのsource_files数を取得"""
    from interfaces.shadow_state_checker import ShadowStateChecker

    checker = ShadowStateChecker()
    result = checker.check("weekly")
    return result.source_count


def run_pattern1(paths: dict[str, Any]) -> DigestEntryResult:
    """Pattern 1: 新Loop検出"""
    new_loops = get_new_loops()
    weekly_source_count = get_weekly_source_count()
    weekly_threshold = paths["weekly_threshold"]

    message = f"新規Loop {len(new_loops)}個を検出" if new_loops else "新規Loopなし"

    return DigestEntryResult(
        status="ok",
        pattern=1,
        base_dir=str(paths["base_dir"]),
        loops_path=str(paths["loops_path"]),
        digests_path=str(paths["digests_path"]),
        essences_path=str(paths["essences_path"]),
        new_loops=new_loops,
        new_loops_count=len(new_loops),
        weekly_source_count=weekly_source_count,
        weekly_threshold=weekly_threshold,
        message=message,
    )


def run_pattern2(paths: dict[str, Any], level: str) -> DigestEntryResult:
    """Pattern 2: 階層確定準備"""
    from interfaces.shadow_state_checker import ShadowStateChecker

    checker = ShadowStateChecker()
    shadow_result = checker.check(level)

    weekly_source_count = get_weekly_source_count()
    weekly_threshold = paths["weekly_threshold"]

    if shadow_result.status == "error":
        return DigestEntryResult(
            status="error",
            pattern=2,
            base_dir=str(paths["base_dir"]),
            level=level,
            error=shadow_result.error,
        )

    message = f"{level} 確定準備: source_files={shadow_result.source_count}個"
    if shadow_result.placeholder_fields:
        message += f", プレースホルダーあり: {shadow_result.placeholder_fields}"

    return DigestEntryResult(
        status="ok",
        pattern=2,
        base_dir=str(paths["base_dir"]),
        loops_path=str(paths["loops_path"]),
        digests_path=str(paths["digests_path"]),
        essences_path=str(paths["essences_path"]),
        level=level,
        shadow_state=asdict(shadow_result),
        weekly_source_count=weekly_source_count,
        weekly_threshold=weekly_threshold,
        message=message,
    )


def format_text_output(result: DigestEntryResult) -> str:
    """テキスト形式で出力をフォーマット"""
    lines = []
    lines.append("```text")
    lines.append("=" * 50)

    if result.pattern == 1:
        lines.append("📂 /digest - 新Loop検出")
    else:
        lines.append(f"📂 /digest {result.level} - 階層確定準備")

    lines.append("=" * 50)
    lines.append("")

    # エラー時
    if result.status == "error":
        lines.append(f"❌ エラー: {result.error}")
        lines.append("```")
        return "\n".join(lines)

    # パス情報
    lines.append("📁 パス情報")
    lines.append(f"  base_dir: {result.base_dir}")
    lines.append(f"  loops_path: {result.loops_path}")
    lines.append(f"  digests_path: {result.digests_path}")
    lines.append("")

    # Pattern 1: 新Loop情報
    if result.pattern == 1:
        lines.append("🔍 新規Loop検出結果")
        if result.new_loops:
            lines.append(f"  検出数: {result.new_loops_count}個")
            for loop in result.new_loops[:10]:  # 最大10件
                lines.append(f"    - {loop}")
            if len(result.new_loops) > 10:
                lines.append(f"    ... 他{len(result.new_loops) - 10}個")
        else:
            lines.append("  新規Loopなし")
        lines.append("")

    # Pattern 2: Shadow状態
    if result.pattern == 2 and result.shadow_state:
        lines.append(f"📊 {result.level} Shadow状態")
        state = result.shadow_state
        lines.append(f"  source_files: {state.get('source_count', 0)}個")
        lines.append(f"  分析済み: {'✅' if state.get('analyzed') else '❌'}")
        if state.get("placeholder_fields"):
            lines.append(f"  プレースホルダー: {state.get('placeholder_fields')}")
        lines.append("")

    # Weekly状況
    lines.append("📈 Weekly状況")
    lines.append(f"  current: {result.weekly_source_count}/{result.weekly_threshold}")
    need = result.weekly_threshold - result.weekly_source_count
    if need > 0:
        lines.append(f"  → あと{need}個でWeekly生成可能")
    else:
        lines.append("  → ✅ Weekly生成可能")
    lines.append("")

    lines.append("=" * 50)
    lines.append("```")
    return "\n".join(lines)


def main() -> None:
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="/digest コマンドエントリポイント",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m interfaces.digest_entry           # Pattern 1: 新Loop検出
    python -m interfaces.digest_entry weekly    # Pattern 2: Weekly確定準備
    python -m interfaces.digest_entry monthly   # Pattern 2: Monthly確定準備
        """,
    )
    parser.add_argument(
        "level",
        nargs="?",
        choices=DIGEST_LEVEL_NAMES,
        default=None,
        help="確定対象レベル（省略時はPattern 1: 新Loop検出）",
    )
    parser.add_argument(
        "--output",
        choices=["json", "text"],
        default="json",
        help="出力形式 (default: json)",
    )

    args = parser.parse_args()

    try:
        paths = get_paths_from_config()

        result = run_pattern1(paths) if args.level is None else run_pattern2(paths, args.level)

    except Exception as e:
        result = DigestEntryResult(
            status="error",
            pattern=1 if args.level is None else 2,
            error=str(e),
        )

    # 出力
    if args.output == "json":
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    else:
        print(format_text_output(result))

    # エラー時は終了コード1
    if result.status == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
