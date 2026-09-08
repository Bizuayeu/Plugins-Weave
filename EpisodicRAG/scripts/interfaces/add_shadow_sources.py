#!/usr/bin/env python3
"""
ShadowGrandDigest source_files 追加スクリプト

指定レベルの overall_digest.source_files にファイル名を追加する。
既登録のファイル名は skip（冪等）。既存分析がある場合は digest_type /
keywords / abstract / impression に触れない。PLACEHOLDER 状態（finalize 直後）
では件数に応じたプレースホルダー文へ更新する（update_shadow_for_new_loops と
同じ FileAppender の挙動。/digest Step 7 が上書きする前提）。

背景:
    /digest Pattern 1 Step 3 は SGD の source_files を Edit ツールで
    直接編集していた。長文日本語 JSON の手編集は事故りやすく、手元の
    書き出しは改行コードも壊しうる。ShadowIO 経由のラウンドトリップで
    安全に追加する。

Usage:
    python -m interfaces.add_shadow_sources <level> <filename> [<filename> ...]

Example:
    python -m interfaces.add_shadow_sources weekly "L00592_講義は顧客の仕様書.txt"

Note:
    filename はファイル名のみ（パス区切り不可）。ファイルの実在は検証しない。
"""

import argparse
import io
import sys
from pathlib import Path

# Windows環境でUTF-8入出力を有効化（CLI実行時のみ）
if sys.platform == "win32" and __name__ == "__main__":
    sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Application層
from application.config import DigestConfig
from application.grand import ShadowGrandDigestManager

# Domain層
from domain.exceptions import EpisodicRAGError
from domain.level_registry import get_level_registry

# Infrastructure層
from infrastructure import get_structured_logger, log_error

_logger = get_structured_logger(__name__)


def validate_filenames(filenames: list[str]) -> None:
    """
    source_files に入れるファイル名の構造を検証

    Args:
        filenames: 追加候補のファイル名

    Raises:
        EpisodicRAGError: 空・パス区切りを含む
    """
    if not filenames:
        raise EpisodicRAGError("ファイル名が指定されていません")
    for name in filenames:
        if not name or not name.strip():
            raise EpisodicRAGError("空のファイル名は指定できません")
        if Path(name).name != name:
            raise EpisodicRAGError(
                f"ファイル名のみを指定してください（パス区切り不可）: {name}"
            )


class ShadowSourceAdder:
    """ShadowGrandDigest の source_files にファイル名を追加するクラス"""

    def __init__(self, config: DigestConfig | None = None):
        """
        Initialize the adder.

        Args:
            config: DigestConfig instance (injected for testability)
        """
        self.config = config or DigestConfig()
        self.manager = ShadowGrandDigestManager(self.config)

    def add_sources(self, level: str, filenames: list[str]) -> list[str]:
        """
        指定レベルの source_files にファイル名を追加して保存

        既登録のファイル名は skip。追加処理は
        ShadowGrandDigestManager.add_files_to_shadow に委譲する。

        Args:
            level: ダイジェストレベル
            filenames: 追加するファイル名（ファイル名のみ）

        Returns:
            実際に追加されたファイル名（指定順、重複除去）

        Raises:
            EpisodicRAGError: 入力不正
        """
        validate_filenames(filenames)
        # FileAppender は呼び出し内の重複を見ない（既存集合を呼び出し前に固定）ため
        # ここで指定順を保って重複除去する
        unique = list(dict.fromkeys(filenames))

        before_digest = self.manager.get_shadow_digest_for_level(level)
        before = set(before_digest["source_files"]) if before_digest else set()

        self.manager.add_files_to_shadow(level, [Path(n) for n in unique])

        after_digest = self.manager.get_shadow_digest_for_level(level)
        after = after_digest["source_files"] if after_digest else []
        return [n for n in after if n not in before]

    @property
    def shadow_digest_file(self) -> Path:
        """保存先 ShadowGrandDigest.txt のパス"""
        return self.manager.shadow_digest_file


def main() -> None:
    """メイン処理"""
    parser = argparse.ArgumentParser(
        description="ShadowGrandDigest source_files 追加スクリプト",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m interfaces.add_shadow_sources weekly "L00592_タイトル.txt"
  python -m interfaces.add_shadow_sources weekly L00592_a.txt L00593_b.txt
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
        "filenames",
        nargs="+",
        help="追加するファイル名（ファイル名のみ、複数可）",
    )
    args = parser.parse_args()

    try:
        adder = ShadowSourceAdder(config=DigestConfig())
        added = adder.add_sources(args.level, args.filenames)

        _logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _logger.info("source_files 追加完了")
        _logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        _logger.info(f"レベル: {args.level}")
        _logger.info(f"追加: {len(added)}件 / 指定: {len(args.filenames)}件")
        for name in added:
            _logger.info(f"  + {name}")
        _logger.info(f"パス: {adder.shadow_digest_file}")
        _logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    except EpisodicRAGError as e:
        log_error(str(e), exit_code=1)
    except OSError as e:
        log_error(f"File I/O error: {e}", exit_code=1)


if __name__ == "__main__":
    main()
