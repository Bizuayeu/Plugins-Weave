#!/usr/bin/env python3
"""
ShadowGrandDigest overall_digest 更新スクリプト

指定レベルの overall_digest 5要素（digest_type / keywords / abstract /
impression / timestamp）を JSON 入力から更新する。source_files は変更しない。

背景:
    overall_digest の abstract は 2400 字級の日本語文字列を含み、
    Edit ツールの exact-match 置換による手動更新は事故りやすい。
    ShadowIO 経由の JSON ラウンドトリップで安全に更新する。

Usage:
    python -m interfaces.update_shadow_overall <level> <json_file>
    python -m interfaces.update_shadow_overall <level> --stdin

入力JSON形式:
    {
      "digest_type": "統合テーマ",
      "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
      "abstract": "統合分析（long版）",
      "impression": "統合所感（long版）"
    }

Note:
    JSONはファイルまたは--stdinで渡してください。
    コマンドライン引数で直接JSON文字列を渡すと、長いテキストが切り詰められる可能性があります。
"""

import argparse
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Windows環境でUTF-8入出力を有効化（CLI実行時のみ）
if sys.platform == "win32" and __name__ == "__main__":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Application層
from application.config import DigestConfig
from application.shadow.shadow_io import ShadowIO
from application.shadow.template import ShadowTemplate

# Domain層
from domain.constants import DIGEST_LEVEL_NAMES
from domain.exceptions import EpisodicRAGError
from domain.file_constants import SHADOW_GRAND_DIGEST_FILENAME
from domain.level_registry import get_level_registry

# Infrastructure層
from infrastructure import get_structured_logger, log_error

_logger = get_structured_logger(__name__)

# 更新対象の必須キー（source_files は含めない＝不変条件）
REQUIRED_KEYS = ("digest_type", "keywords", "abstract", "impression")


def validate_overall_payload(payload: dict[str, Any]) -> None:
    """
    overall_digest 更新入力の構造を検証

    Args:
        payload: 入力JSON（4要素）

    Raises:
        EpisodicRAGError: 必須キー欠落・型不正
    """
    missing = [k for k in REQUIRED_KEYS if k not in payload]
    if missing:
        raise EpisodicRAGError(f"必須キーが欠落しています: {missing}")

    if not isinstance(payload["keywords"], list):
        raise EpisodicRAGError("keywords はリストである必要があります")

    for key in ("digest_type", "abstract", "impression"):
        if not isinstance(payload[key], str):
            raise EpisodicRAGError(f"{key} は文字列である必要があります")


class OverallDigestUpdater:
    """ShadowGrandDigest の overall_digest 5要素を更新するクラス"""

    def __init__(self, config: DigestConfig | None = None):
        """
        Initialize the updater.

        Args:
            config: DigestConfig instance (injected for testability)
        """
        self.config = config or DigestConfig()
        template = ShadowTemplate(DIGEST_LEVEL_NAMES)
        self.shadow_io = ShadowIO(
            self.config.essences_path / SHADOW_GRAND_DIGEST_FILENAME,
            template_factory=template.get_template,
        )

    def update_overall(self, level: str, payload: dict[str, Any]) -> Path:
        """
        指定レベルの overall_digest を更新して保存

        source_files には触れない。overall_digest.timestamp と
        metadata.last_updated（ShadowIO.save が自動更新）を現在時刻にする。

        Args:
            level: ダイジェストレベル
            payload: 4要素の入力JSON

        Returns:
            保存した ShadowGrandDigest.txt のパス

        Raises:
            EpisodicRAGError: 入力不正・レベル不在
        """
        validate_overall_payload(payload)

        data = self.shadow_io.load_or_create()

        latest = data.get("latest_digests", {})
        if level not in latest:
            raise EpisodicRAGError(f"ShadowGrandDigest にレベルがありません: {level}")

        overall = latest[level]["overall_digest"]
        if overall is None:
            raise EpisodicRAGError(f"overall_digest が未初期化です: {level}")
        overall["digest_type"] = payload["digest_type"]
        overall["keywords"] = payload["keywords"]
        overall["abstract"] = payload["abstract"]
        overall["impression"] = payload["impression"]
        overall["timestamp"] = datetime.now().isoformat()

        self.shadow_io.save(data)
        return self.shadow_io.shadow_digest_file


def main() -> None:
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="ShadowGrandDigest overall_digest 更新スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m interfaces.update_shadow_overall monthly overall_payload.json
  cat payload.json | python -m interfaces.update_shadow_overall monthly --stdin
        """,
    )
    # Registry経由でレベル一覧を動的に取得（OCP準拠）
    registry = get_level_registry()
    parser.add_argument(
        "level",
        choices=registry.get_level_names(),
        help="ダイジェストレベル",
    )
    parser.add_argument(
        "input_data",
        nargs="?",
        default=None,
        help="JSONファイルパス（--stdin使用時は不要）",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="標準入力からJSONを読み込む（長いJSONに推奨）",
    )
    args = parser.parse_args()

    if not args.stdin and args.input_data is None:
        parser.error("input_data is required unless --stdin is specified")

    try:
        raw = (
            sys.stdin.read()
            if args.stdin
            else Path(args.input_data).read_text(encoding="utf-8")
        )
        payload = json.loads(raw)

        updater = OverallDigestUpdater(config=DigestConfig())
        saved_path = updater.update_overall(args.level, payload)

        _logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _logger.info("overall_digest 更新完了")
        _logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _logger.info(f"レベル: {args.level}")
        _logger.info(f"digest_type: {payload['digest_type']}")
        _logger.info(f"keywords: {len(payload['keywords'])}件")
        _logger.info(f"abstract: {len(payload['abstract'])}文字")
        _logger.info(f"impression: {len(payload['impression'])}文字")
        _logger.info(f"パス: {saved_path}")
        _logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    except FileNotFoundError as e:
        log_error(f"File not found: {e}", exit_code=1)
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON format: {e}", exit_code=1)
    except EpisodicRAGError as e:
        log_error(str(e), exit_code=1)
    except OSError as e:
        log_error(f"File I/O error: {e}", exit_code=1)


if __name__ == "__main__":
    main()
