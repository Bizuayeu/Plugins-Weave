#!/usr/bin/env python3
"""
File Appender
=============

ファイル追加処理（Shadowへの増分追加）
"""
from pathlib import Path
from typing import Dict, List

from domain.types import ShadowDigestData, OverallDigestData, LevelHierarchyEntry
from domain.constants import SOURCE_TYPE_LOOPS
from infrastructure import log_info, log_warning, read_json_from_file_safe
from application.validators import is_valid_dict

from .template import ShadowTemplate
from .file_detector import FileDetector
from .shadow_io import ShadowIO
from .placeholder_manager import PlaceholderManager


class FileAppender:
    """ファイル追加処理クラス"""

    def __init__(
        self,
        shadow_io: ShadowIO,
        file_detector: FileDetector,
        template: ShadowTemplate,
        level_hierarchy: Dict[str, LevelHierarchyEntry],
        placeholder_manager: PlaceholderManager
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
        self,
        shadow_data: ShadowDigestData,
        level: str
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

        digest_data = read_json_from_file_safe(full_path)
        if digest_data is None:
            return

        if not is_valid_dict(digest_data):
            log_warning(f"{file_path.name} is not a dict, skipping")
            return

        overall = digest_data.get("overall_digest")
        if not is_valid_dict(overall):
            overall = {}

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

        # 新しいファイルだけをsource_filesに追加
        for file_path in new_files:
            if file_path.name not in existing_files:
                overall_digest["source_files"].append(file_path.name)
                log_info(f"  + {file_path.name}")

                # Monthly以上: Digestファイルの内容を読み込んでログ出力
                if source_type != SOURCE_TYPE_LOOPS:
                    self._log_digest_content(file_path, level)

        # PLACEHOLDERの更新または既存分析の保持
        total_files = len(overall_digest["source_files"])
        self.placeholder_manager.update_or_preserve(overall_digest, total_files)

        self.shadow_io.save(shadow_data)
