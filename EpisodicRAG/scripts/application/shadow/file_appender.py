#!/usr/bin/env python3
"""
File Appender
=============

ファイル追加処理（Shadowへの増分追加）
"""

from pathlib import Path
from typing import Dict, List, Set

from application.validators import is_valid_dict
from domain.constants import (
    LOG_PREFIX_DECISION,
    LOG_PREFIX_FILE,
    LOG_PREFIX_STATE,
    LOG_PREFIX_VALIDATE,
    SOURCE_TYPE_LOOPS,
)
from domain.types import LevelHierarchyEntry, OverallDigestData, ShadowDigestData
from infrastructure import log_debug, log_info, log_warning, try_read_json_from_file

from .file_detector import FileDetector
from .placeholder_manager import PlaceholderManager
from .shadow_io import ShadowIO
from .template import ShadowTemplate


class FileAppender:
    """ファイル追加処理クラス"""

    def __init__(
        self,
        shadow_io: ShadowIO,
        file_detector: FileDetector,
        template: ShadowTemplate,
        level_hierarchy: Dict[str, LevelHierarchyEntry],
        placeholder_manager: PlaceholderManager,
    ):
        """
        初期化

        Args:
            shadow_io: ShadowIO インスタンス
            file_detector: FileDetector インスタンス
            template: ShadowTemplate インスタンス
            level_hierarchy: レベル階層情報
            placeholder_manager: PlaceholderManager インスタンス
        """
        self.shadow_io = shadow_io
        self.file_detector = file_detector
        self.template = template
        self.level_hierarchy = level_hierarchy
        self.placeholder_manager = placeholder_manager

    def _ensure_overall_digest_initialized(
        self, shadow_data: ShadowDigestData, level: str
    ) -> OverallDigestData:
        """
        overall_digestの初期化を確保

        Args:
            shadow_data: ShadowGrandDigestデータ
            level: レベル名

        Returns:
            初期化済みのoverall_digest
        """
        overall_digest = shadow_data["latest_digests"][level]["overall_digest"]

        log_debug(f"{LOG_PREFIX_STATE} _ensure_overall_digest_initialized: level={level}")
        log_debug(
            f"{LOG_PREFIX_VALIDATE} overall_digest: is_none={overall_digest is None}, is_valid={is_valid_dict(overall_digest) if overall_digest else False}"
        )

        # overall_digestがnullまたは非dict型の場合、初期化
        if overall_digest is None or not is_valid_dict(overall_digest):
            log_debug(f"{LOG_PREFIX_DECISION} reinitializing overall_digest (null or invalid)")
            overall_digest = self.template.create_empty_overall_digest()
            shadow_data["latest_digests"][level]["overall_digest"] = overall_digest

        # source_filesがoverall_digest内に存在しない場合、初期化
        if "source_files" not in overall_digest:
            log_debug(f"{LOG_PREFIX_DECISION} initializing source_files (not present)")
            overall_digest["source_files"] = []

        return overall_digest

    def _add_new_files_to_digest(
        self,
        overall_digest: OverallDigestData,
        new_files: List[Path],
        existing_files: Set[str],
    ) -> int:
        """
        新規ファイルをoverall_digestに追加

        Args:
            overall_digest: 追加先のダイジェスト
            new_files: 追加候補のファイルリスト
            existing_files: 既存ファイル名のセット

        Returns:
            追加されたファイル数
        """
        added_count = 0
        for file_path in new_files:
            if file_path.name not in existing_files:
                overall_digest["source_files"].append(file_path.name)
                added_count += 1
                log_info(f"  + {file_path.name}")
            else:
                log_debug(f"{LOG_PREFIX_FILE} skipped (already exists): {file_path.name}")
        return added_count

    def _log_digest_contents_for_level(
        self,
        new_files: List[Path],
        existing_files: Set[str],
        level: str,
        source_type: str,
    ) -> None:
        """
        Monthly以上のレベルでDigestファイル内容をログ出力

        Args:
            new_files: 追加されたファイルリスト
            existing_files: 既存ファイル名のセット
            level: レベル名
            source_type: ソースタイプ
        """
        if source_type == SOURCE_TYPE_LOOPS:
            return

        for file_path in new_files:
            if file_path.name not in existing_files:
                self._log_digest_content(file_path, level)

    def _log_digest_content(self, file_path: Path, level: str) -> None:
        """
        Digestファイルの内容を読み込んでログ出力（Monthly以上用）

        Args:
            file_path: ファイルパス
            level: レベル名
        """
        source_dir = self.file_detector.get_source_path(level)
        full_path = source_dir / file_path.name

        digest_data = try_read_json_from_file(full_path)
        if digest_data is None:
            return

        if not is_valid_dict(digest_data):
            log_warning(f"{file_path.name} is not a dict, skipping")
            return

        overall_raw = digest_data.get("overall_digest")
        overall = overall_raw if isinstance(overall_raw, dict) else {}

        log_info(f"Read digest content from {file_path.name}")
        log_info(f"      - digest_type: {overall.get('digest_type', 'N/A')}")
        log_info(f"      - keywords: {len(overall.get('keywords', []))} items")
        log_info(f"      - abstract: {len(overall.get('abstract', ''))} chars")
        log_info(f"      - impression: {len(overall.get('impression', ''))} chars")

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

        log_debug(
            f"{LOG_PREFIX_STATE} add_files_to_shadow: level={level}, new_files_count={len(new_files)}"
        )
        log_debug(f"{LOG_PREFIX_STATE} existing_files_count: {len(existing_files)}")
        log_debug(f"{LOG_PREFIX_STATE} source_type: {source_type}")

        # ファイル追加
        added_count = self._add_new_files_to_digest(overall_digest, new_files, existing_files)

        # ログ出力（Monthly以上）
        self._log_digest_contents_for_level(new_files, existing_files, level, source_type)

        log_debug(f"{LOG_PREFIX_STATE} files_added: {added_count}")

        # PLACEHOLDERの更新または既存分析の保持
        total_files = len(overall_digest["source_files"])
        log_debug(f"{LOG_PREFIX_STATE} total_files_after_add: {total_files}")
        self.placeholder_manager.update_or_preserve(overall_digest, total_files)

        self.shadow_io.save(shadow_data)
