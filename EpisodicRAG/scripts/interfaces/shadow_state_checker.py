#!/usr/bin/env python3
"""
Shadow State Checker CLI
========================

Shadow状態判定CLI。Claudeから呼び出され、ShadowGrandDigestの
プレースホルダー有無を確認し、DigestAnalyzer起動が必要かを判定する。

Usage:
    python -m interfaces.shadow_state_checker weekly
    python -m interfaces.shadow_state_checker monthly
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain.exceptions import FileIOError
from domain.file_constants import CONFIG_FILENAME, SHADOW_GRAND_DIGEST_FILENAME
from infrastructure.config import get_persistent_config_dir
from infrastructure.json_repository import load_json

# Windows UTF-8対応（pytest実行時はスキップ）
if sys.platform == "win32" and "pytest" not in sys.modules:
    import io

    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


# プレースホルダーマーカー
PLACEHOLDER_MARKER = "<!-- PLACEHOLDER -->"


@dataclass
class ShadowStateResult:
    """Shadow状態確認結果"""

    status: str  # "ok" | "error"
    level: str
    analyzed: bool  # True: 分析済み, False: プレースホルダーあり
    source_files: List[str] = field(default_factory=list)
    source_count: int = 0
    placeholder_fields: List[str] = field(default_factory=list)
    message: str = ""
    error: Optional[str] = None


class ShadowStateChecker:
    """Shadow状態確認クラス"""

    LEVEL_NAMES = [
        "weekly",
        "monthly",
        "quarterly",
        "annual",
        "triennial",
        "decadal",
        "multi_decadal",
        "centurial",
    ]

    def __init__(self) -> None:
        """Initialize ShadowStateChecker"""
        self.config_file = get_persistent_config_dir() / CONFIG_FILENAME
        self.shadow_file: Optional[Path] = None

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        return load_json(self.config_file)

    def _get_essences_path(self, config: Dict[str, Any]) -> Path:
        """Essencesパスを取得"""
        base_dir = config.get("base_dir", "")
        if not base_dir:
            raise ValueError("base_dir is required in config.json")
        base_path = Path(base_dir).expanduser().resolve()

        paths = config.get("paths", {})
        essences_dir = str(paths.get("essences_dir", "data/Essences"))
        return base_path / essences_dir

    def _load_shadow(self) -> Dict[str, Any]:
        """ShadowGrandDigest.txtを読み込む"""
        if self.shadow_file is None:
            raise ValueError("Shadow file path not set")

        return load_json(self.shadow_file)

    def _has_placeholder(self, text: Optional[str]) -> bool:
        """プレースホルダー有無を判定"""
        if text is None:
            return True  # null もプレースホルダー扱い
        return PLACEHOLDER_MARKER in text

    def check(self, level: str) -> ShadowStateResult:
        """
        指定レベルのShadow状態を確認

        Args:
            level: 確認対象レベル（"weekly", "monthly"等）

        Returns:
            ShadowStateResult: 状態確認結果
        """
        # レベル検証
        if level not in self.LEVEL_NAMES:
            return ShadowStateResult(
                status="error",
                level=level,
                analyzed=False,
                error=f"Invalid level: {level}. Valid levels: {', '.join(self.LEVEL_NAMES)}",
            )

        try:
            # 設定読み込み
            config = self._load_config()
            essences_path = self._get_essences_path(config)
            self.shadow_file = essences_path / SHADOW_GRAND_DIGEST_FILENAME

            # Shadow読み込み
            shadow_data = self._load_shadow()

            # 指定レベルのデータを取得
            latest_digests = shadow_data.get("latest_digests", {})
            level_data = latest_digests.get(level, {})

            if not level_data:
                return ShadowStateResult(
                    status="ok",
                    level=level,
                    analyzed=True,
                    source_files=[],
                    source_count=0,
                    placeholder_fields=[],
                    message=f"No data for level: {level}",
                )

            # overall_digestを取得（Noneの場合は空辞書として扱う）
            overall_digest = level_data.get("overall_digest") or {}
            source_files = overall_digest.get("source_files", [])

            # プレースホルダー確認
            placeholder_fields = []
            abstract = overall_digest.get("abstract")
            impression = overall_digest.get("impression")
            digest_type = overall_digest.get("digest_type")
            keywords = overall_digest.get("keywords")

            if self._has_placeholder(abstract):
                placeholder_fields.append("abstract")
            if self._has_placeholder(impression):
                placeholder_fields.append("impression")
            if self._has_placeholder(digest_type):
                placeholder_fields.append("digest_type")
            if keywords is None or (isinstance(keywords, list) and len(keywords) == 0):
                placeholder_fields.append("keywords")

            analyzed = len(placeholder_fields) == 0

            if analyzed:
                message = "All fields analyzed"
            else:
                message = f"Placeholders detected in: {', '.join(placeholder_fields)} - run DigestAnalyzer"

            return ShadowStateResult(
                status="ok",
                level=level,
                analyzed=analyzed,
                source_files=source_files,
                source_count=len(source_files),
                placeholder_fields=placeholder_fields,
                message=message,
            )

        except FileIOError as e:
            return ShadowStateResult(
                status="error",
                level=level,
                analyzed=False,
                error=str(e),
            )
        except Exception as e:
            return ShadowStateResult(
                status="error",
                level=level,
                analyzed=False,
                error=f"Unexpected error: {e}",
            )


def main() -> None:
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Shadow状態確認CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m interfaces.shadow_state_checker weekly
    python -m interfaces.shadow_state_checker monthly
        """,
    )
    parser.add_argument(
        "level",
        choices=ShadowStateChecker.LEVEL_NAMES,
        help="確認対象レベル",
    )
    args = parser.parse_args()

    # チェック実行
    checker = ShadowStateChecker()
    result = checker.check(args.level)

    # JSON出力
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))

    # エラー時は終了コード1
    if result.status == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
