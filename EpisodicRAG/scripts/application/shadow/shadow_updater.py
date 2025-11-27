#!/usr/bin/env python3
"""
Shadow Updater
==============

ShadowGrandDigestの更新、カスケード処理を担当
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from domain.constants import PLACEHOLDER_LIMITS, PLACEHOLDER_MARKER, PLACEHOLDER_END
from infrastructure import log_info, log_warning
from application.validators import is_valid_dict

from .template import ShadowTemplate
from .file_detector import FileDetector
from .shadow_io import ShadowIO


class ShadowUpdater:
    """ShadowGrandDigest更新クラス"""

    def __init__(
        self,
        shadow_io: ShadowIO,
        file_detector: FileDetector,
        template: ShadowTemplate,
        level_hierarchy: Dict[str, Dict[str, Any]]
    ):
        """
        初期化

        Args:
            shadow_io: ShadowIO インスタンス
            file_detector: FileDetector インスタンス
            template: ShadowTemplate インスタンス
            level_hierarchy: レベル階層情報
        """
        self.shadow_io = shadow_io
        self.file_detector = file_detector
        self.template = template
        self.level_hierarchy = level_hierarchy

    def _ensure_overall_digest_initialized(
        self,
        shadow_data: Dict[str, Any],
        level: str
    ) -> Dict[str, Any]:
        """
        overall_digestの初期化を確保

        Args:
            shadow_data: ShadowGrandDigestデータ
            level: レベル名

        Returns:
            初期化済みのoverall_digest
        """
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        # overall_digestがnullまたは非dict型の場合、初期化
        if overall_digest is None or not is_valid_dict(overall_digest):
            overall_digest = self.template.create_empty_overall_digest()
            shadow_data["latest_digests"][level]["overall_digest"] = overall_digest

        # source_filesがoverall_digest内に存在しない場合、初期化
        if "source_files" not in overall_digest:
            overall_digest["source_files"] = []

        return overall_digest

    def _log_digest_content(self, file_path: Path, level: str) -> None:
        """
        Digestファイルの内容を読み込んでログ出力（Monthly以上用）

        Args:
            file_path: ファイルパス
            level: レベル名
        """
        source_dir = self.file_detector.get_source_path(level)
        full_path = source_dir / file_path.name

        if not (full_path.exists() and full_path.suffix == '.txt'):
            return

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                digest_data = json.load(f)

            if not is_valid_dict(digest_data):
                log_warning(f"{file_path.name} is not a dict, skipping")
                return

            overall = digest_data.get("overall_digest")
            if not is_valid_dict(overall):
                overall = {}

            log_info(f"Read digest content from {file_path.name}")
            print(f"      - digest_type: {overall.get('digest_type', 'N/A')}")
            print(f"      - keywords: {len(overall.get('keywords', []))} items")
            print(f"      - abstract: {len(overall.get('abstract', ''))} chars")
            print(f"      - impression: {len(overall.get('impression', ''))} chars")

        except json.JSONDecodeError:
            log_warning(f"Failed to parse {file_path.name} as JSON")
        except OSError as e:
            log_warning(f"Error reading {file_path.name}: {e}")

    def _update_placeholder_or_preserve(
        self,
        overall_digest: Dict[str, Any],
        total_files: int
    ) -> None:
        """
        PLACEHOLDERの更新または既存分析の保持

        Args:
            overall_digest: overall_digestデータ
            total_files: 総ファイル数
        """
        abstract = overall_digest.get("abstract", "")
        is_placeholder = (
            not abstract or
            (isinstance(abstract, str) and PLACEHOLDER_MARKER in abstract)
        )

        if is_placeholder:
            limits = PLACEHOLDER_LIMITS
            overall_digest["abstract"] = (
                f"{PLACEHOLDER_MARKER}: {total_files}ファイル分の全体統合分析 "
                f"({limits['abstract_chars']}文字程度){PLACEHOLDER_END}"
            )
            overall_digest["impression"] = (
                f"{PLACEHOLDER_MARKER}: 所感・展望 "
                f"({limits['impression_chars']}文字程度){PLACEHOLDER_END}"
            )
            overall_digest["keywords"] = [
                f"{PLACEHOLDER_MARKER}: keyword{i}{PLACEHOLDER_END}"
                for i in range(1, limits["keyword_count"] + 1)
            ]
            log_info(f"Initialized placeholder for {total_files} file(s)")
        else:
            log_info(f"Preserved existing analysis (now {total_files} file(s) total)")
            log_info(f"Claude should re-analyze all {total_files} files to integrate new content")

    def add_files_to_shadow(self, level: str, new_files: List[Path]) -> None:
        """
        指定レベルのShadowに新しいファイルを追加（増分更新）

        Weekly: source_filesのみ追加（PLACEHOLDERのまま）→ Claude分析待ち
        Monthly以上: Digestファイル内容を読み込んでログ出力（まだらボケ回避）

        Args:
            level: レベル名
            new_files: 追加するファイルのリスト
        """
        shadow_data = self.shadow_io.load_or_create()
        overall_digest = self._ensure_overall_digest_initialized(shadow_data, level)

        existing_files = set(overall_digest["source_files"])
        source_type = self.level_hierarchy[level]["source"]

        # 新しいファイルだけをsource_filesに追加
        for file_path in new_files:
            if file_path.name not in existing_files:
                overall_digest["source_files"].append(file_path.name)
                print(f"  + {file_path.name}")

                # Monthly以上: Digestファイルの内容を読み込んでログ出力
                if source_type != "loops":
                    self._log_digest_content(file_path, level)

        # PLACEHOLDERの更新または既存分析の保持
        total_files = len(overall_digest["source_files"])
        self._update_placeholder_or_preserve(overall_digest, total_files)

        self.shadow_io.save(shadow_data)

    def clear_shadow_level(self, level: str) -> None:
        """
        指定レベルのShadowを初期化

        Args:
            level: レベル名
        """
        shadow_data = self.shadow_io.load_or_create()

        # overall_digestを空のプレースホルダーにリセット
        shadow_data["latest_digests"][level]["overall_digest"] = self.template.create_empty_overall_digest()

        self.shadow_io.save(shadow_data)
        log_info(f"Cleared ShadowGrandDigest for level: {level}")

    def get_shadow_digest_for_level(self, level: str) -> Optional[Dict[str, Any]]:
        """
        指定レベルのShadowダイジェストを取得

        finalize_from_shadow.pyで使用: これがRegularDigestの内容になります

        Args:
            level: レベル名

        Returns:
            overall_digestデータ、またはNone
        """
        shadow_data = self.shadow_io.load_or_create()
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        if not overall_digest or not overall_digest.get("source_files"):
            log_info(f"No shadow digest for level: {level}")
            return None

        return overall_digest

    def promote_shadow_to_grand(self, level: str) -> None:
        """
        ShadowのレベルをGrandDigestに昇格

        注意: この機能は実際にはfinalize_from_shadow.pyの処理2で
        GrandDigestManagerが実行します。ここでは確認のみ。

        Args:
            level: レベル名
        """
        digest = self.get_shadow_digest_for_level(level)

        if not digest:
            log_info(f"No shadow digest to promote for level: {level}")
            return

        file_count = len(digest.get("source_files", []))
        log_info(f"Shadow digest ready for promotion: {file_count} file(s)")
        # 実際の昇格処理はfinalize_from_shadow.pyで実行される

    def update_shadow_for_new_loops(self) -> None:
        """新しいLoopファイルを検出してShadowを増分更新"""
        # Shadowファイルを読み込み（存在しなければ作成）
        self.shadow_io.load_or_create()

        new_files = self.file_detector.find_new_files("weekly")

        if not new_files:
            log_info("No new Loop files found")
            return

        log_info(f"Found {len(new_files)} new Loop file(s):")

        # Shadowに増分追加
        self.add_files_to_shadow("weekly", new_files)

    def cascade_update_on_digest_finalize(self, level: str) -> None:
        """
        ダイジェスト確定時のカスケード処理（処理3）

        処理内容:
        1. 現在のレベルのShadow → Grand に昇格（確認のみ、実際は処理2で完了）
        2. 次のレベルの新しいファイルを検出
        3. 次のレベルのShadowに増分追加
        4. 現在のレベルのShadowをクリア

        Args:
            level: レベル名
        """
        print(f"\n[処理3] ShadowGrandDigest cascade for level: {level}")

        # 1. Shadow → Grand 昇格の確認
        self.promote_shadow_to_grand(level)

        # 2. 次のレベルの新しいファイルを検出
        next_level = self.level_hierarchy[level]["next"]
        if next_level:
            new_files = self.file_detector.find_new_files(next_level)

            if new_files:
                log_info(f"Found {len(new_files)} new file(s) for {next_level}:")

                # 3. 次のレベルのShadowに増分追加
                self.add_files_to_shadow(next_level, new_files)
        else:
            log_info(f"No next level for {level} (top level)")

        # 4. 現在のレベルのShadowをクリア
        self.clear_shadow_level(level)

        print(f"[処理3] Cascade completed for level: {level}")
