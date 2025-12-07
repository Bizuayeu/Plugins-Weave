#!/usr/bin/env python3
"""
Digest Readiness Checker CLI
=============================

Digest確定可否判定CLI。Claudeから呼び出され、
SDGとProvisionalの完備状態を確認し、Digest確定が可能かを判定する。

Usage:
    python -m interfaces.digest_readiness weekly
    python -m interfaces.digest_readiness monthly
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from application.config import DigestConfig
from domain.constants import DIGEST_LEVEL_NAMES, PLACEHOLDER_MARKER
from domain.file_constants import SHADOW_GRAND_DIGEST_FILENAME
from infrastructure.json_repository import load_json

# Windows UTF-8対応（pytest実行時はスキップ）
if sys.platform == "win32" and "pytest" not in sys.modules:
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


@dataclass
class DigestReadinessResult:
    """Digest確定可否判定結果"""

    status: str  # "ok" | "error"
    level: str
    source_count: int = 0
    level_threshold: int = 5
    threshold_met: bool = False
    sdg_ready: bool = False
    missing_sdg_files: List[str] = field(default_factory=list)
    provisional_ready: bool = False
    missing_provisionals: List[str] = field(default_factory=list)
    can_finalize: bool = False
    blockers: List[str] = field(default_factory=list)
    message: str = ""
    error: Optional[str] = None


class DigestReadinessChecker:
    """Digest確定可否判定クラス"""

    def __init__(self, plugin_root: Optional[Path] = None):
        """
        Args:
            plugin_root: Pluginルート（指定しない場合は自動検出）
        """
        if plugin_root:
            self.plugin_root = Path(plugin_root).resolve()
        else:
            self.plugin_root = Path(__file__).resolve().parent.parent.parent

        self.config = DigestConfig(plugin_root=self.plugin_root)

    def check(self, level: str) -> DigestReadinessResult:
        """
        指定レベルのDigest確定可否を判定

        Args:
            level: 確認対象レベル（"weekly", "monthly"等）

        Returns:
            DigestReadinessResult: 判定結果
        """
        # レベル検証
        if level not in DIGEST_LEVEL_NAMES:
            return DigestReadinessResult(
                status="error",
                level=level,
                error=f"Invalid level: {level}. Valid levels: {', '.join(DIGEST_LEVEL_NAMES)}",
            )

        try:
            # 基本情報取得
            level_threshold = self.config._threshold_provider.get_threshold(level)

            # SDG読み込み
            shadow_path = self.config.essences_path / SHADOW_GRAND_DIGEST_FILENAME
            shadow_data = load_json(shadow_path)

            # 対象レベルのデータ取得
            latest_digests = shadow_data.get("latest_digests", {})
            level_data = latest_digests.get(level, {})
            overall_digest = level_data.get("overall_digest") or {}
            source_files = overall_digest.get("source_files", [])
            source_count = len(source_files)

            # threshold判定
            threshold_met = source_count >= level_threshold

            # SDG完備判定
            sdg_ready, missing_sdg_files = self._check_sdg_ready(overall_digest, source_files)

            # Provisional完備判定
            provisional_ready, missing_provisionals = self._check_provisional_ready(
                level, source_files
            )

            # can_finalize判定
            can_finalize = threshold_met and sdg_ready and provisional_ready

            # blockers生成
            blockers = self._generate_blockers(
                threshold_met,
                source_count,
                level_threshold,
                sdg_ready,
                missing_sdg_files,
                overall_digest,
                provisional_ready,
                missing_provisionals,
            )

            # メッセージ生成
            if can_finalize:
                message = "Digest確定可能"
            else:
                message = f"Digest確定不可: {len(blockers)}件の未達条件あり"

            return DigestReadinessResult(
                status="ok",
                level=level,
                source_count=source_count,
                level_threshold=level_threshold,
                threshold_met=threshold_met,
                sdg_ready=sdg_ready,
                missing_sdg_files=missing_sdg_files,
                provisional_ready=provisional_ready,
                missing_provisionals=missing_provisionals,
                can_finalize=can_finalize,
                blockers=blockers,
                message=message,
            )

        except Exception as e:
            return DigestReadinessResult(
                status="error",
                level=level,
                error=f"Unexpected error: {e}",
            )

    def _check_sdg_ready(
        self, overall_digest: Dict[str, Any], source_files: List[str]
    ) -> tuple[bool, List[str]]:
        """
        SDG完備状態を判定

        SDG完備 = overall_digest存在 AND 4要素がPLACEHOLDERでない

        Returns:
            (sdg_ready, missing_sdg_files)
        """
        if not overall_digest:
            return False, []

        # 4要素のPLACEHOLDER確認
        has_placeholder = any(
            [
                self._has_placeholder(overall_digest.get("digest_type", "")),
                self._has_placeholder(overall_digest.get("abstract", "")),
                self._has_placeholder(overall_digest.get("impression", "")),
                self._keywords_has_placeholder(overall_digest.get("keywords", [])),
            ]
        )

        if has_placeholder:
            return False, []

        return True, []

    def _has_placeholder(self, text: Optional[str]) -> bool:
        """テキストにPLACEHOLDERが含まれるか判定"""
        if text is None:
            return True
        if isinstance(text, str) and PLACEHOLDER_MARKER in text:
            return True
        return False

    def _keywords_has_placeholder(self, keywords: Optional[List[str]]) -> bool:
        """keywordsにPLACEHOLDERが含まれるか判定"""
        if keywords is None:
            return True
        if len(keywords) == 0:
            return True
        for kw in keywords:
            if self._has_placeholder(kw):
                return True
        return False

    def _check_provisional_ready(
        self, level: str, source_files: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Provisional完備状態を判定

        Provisional完備 = Provisionalファイル存在
                         AND source_files全てにindividual_digestsエントリ存在

        Returns:
            (provisional_ready, missing_provisionals)
        """
        if not source_files:
            return True, []

        try:
            # Provisionalディレクトリ取得
            provisional_dir = self.config.get_provisional_dir(level)

            # Provisionalファイル検索
            provisional_files = list(provisional_dir.glob("*_Individual.txt"))
            if not provisional_files:
                return False, list(source_files)

            # 最新のProvisionalファイルを読み込み
            latest_provisional = max(provisional_files, key=lambda p: p.stat().st_mtime)
            provisional_data = load_json(latest_provisional)
            individual_digests = provisional_data.get("individual_digests", [])

            # source_filesのうちindividual_digestsに存在しないものを検出
            existing_files = {d.get("source_file") for d in individual_digests}
            missing = [f for f in source_files if f not in existing_files]

            if missing:
                return False, missing

            return True, []

        except Exception:
            return False, list(source_files)

    def _generate_blockers(
        self,
        threshold_met: bool,
        source_count: int,
        level_threshold: int,
        sdg_ready: bool,
        missing_sdg_files: List[str],
        overall_digest: Dict[str, Any],
        provisional_ready: bool,
        missing_provisionals: List[str],
    ) -> List[str]:
        """未達条件のblockerリストを生成"""
        blockers = []

        if not threshold_met:
            need = level_threshold - source_count
            blockers.append(
                f"threshold未達: {source_count}/{level_threshold} (あと{need}ファイル必要)"
            )

        if not sdg_ready:
            # PLACEHOLDERがある場合
            placeholder_fields = []
            if self._has_placeholder(overall_digest.get("digest_type")):
                placeholder_fields.append("digest_type")
            if self._has_placeholder(overall_digest.get("abstract")):
                placeholder_fields.append("abstract")
            if self._has_placeholder(overall_digest.get("impression")):
                placeholder_fields.append("impression")
            if self._keywords_has_placeholder(overall_digest.get("keywords")):
                placeholder_fields.append("keywords")

            if placeholder_fields:
                blockers.append(f"SDG未完備: PLACEHOLDERあり ({', '.join(placeholder_fields)})")
            elif missing_sdg_files:
                blockers.append("SDG未完備: source_filesに未登録ファイルあり")

        if not provisional_ready:
            if missing_provisionals:
                blockers.append(f"Provisional未完備: {', '.join(missing_provisionals)} が不足")
            else:
                blockers.append("Provisional未完備: Provisionalファイルなし")

        return blockers


def main() -> None:
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Digest確定可否判定CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m interfaces.digest_readiness weekly
    python -m interfaces.digest_readiness monthly
        """,
    )
    parser.add_argument(
        "level",
        choices=DIGEST_LEVEL_NAMES,
        help="確認対象レベル",
    )
    parser.add_argument(
        "--plugin-root",
        type=str,
        default=None,
        help="Pluginルートパス（デフォルト: 自動検出）",
    )

    args = parser.parse_args()

    # チェック実行
    plugin_root = Path(args.plugin_root) if args.plugin_root else None
    checker = DigestReadinessChecker(plugin_root=plugin_root)
    result = checker.check(args.level)

    # JSON出力
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))

    # エラー時は終了コード1
    if result.status == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()
