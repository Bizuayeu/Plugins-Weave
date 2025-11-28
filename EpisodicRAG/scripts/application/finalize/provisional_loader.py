#!/usr/bin/env python3
"""
Provisional Loader
==================

ProvisionalDigestの読み込みまたはソースファイルからの自動生成
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from application.grand import ShadowGrandDigestManager
from application.validators import is_valid_dict
from config import DigestConfig
from domain.constants import (
    LEVEL_CONFIG,
    LOG_PREFIX_DECISION,
    LOG_PREFIX_FILE,
    LOG_PREFIX_STATE,
    LOG_PREFIX_VALIDATE,
)
from domain.error_formatter import get_error_formatter
from domain.exceptions import DigestError
from domain.types import IndividualDigestData, OverallDigestData
from infrastructure import load_json, log_debug, log_info, log_warning, try_read_json_from_file


class ProvisionalLoader:
    """ProvisionalDigestの読み込みと自動生成を担当"""

    def __init__(self, config: DigestConfig, shadow_manager: ShadowGrandDigestManager):
        """
        Args:
            config: DigestConfig インスタンス
            shadow_manager: ShadowGrandDigestManager インスタンス
        """
        self.config = config
        self.shadow_manager = shadow_manager
        self.level_config = LEVEL_CONFIG

    def _get_source_path_for_level(self, level: str) -> Path:
        """
        指定レベルのソースファイルディレクトリを取得

        Args:
            level: ダイジェストレベル

        Returns:
            ソースファイルのディレクトリパス
        """
        # 統一メソッドを使用
        return self.config.get_source_dir(level)

    def _get_provisional_path(self, level: str, digest_num: str) -> Path:
        """
        Provisionalファイルのパスを取得

        Args:
            level: ダイジェストレベル
            digest_num: ダイジェスト番号（ゼロ埋め済み）

        Returns:
            Provisionalファイルのパス
        """
        level_cfg = self.level_config[level]
        provisional_dir = self.config.get_provisional_dir(level)
        return provisional_dir / f"{level_cfg['prefix']}{digest_num}_Individual.txt"

    def _load_provisional(self, provisional_path: Path) -> Tuple[List[IndividualDigestData], Path]:
        """
        Provisionalファイルを読み込んで検証

        Args:
            provisional_path: Provisionalファイルのパス

        Returns:
            (individual_digests, provisional_file_to_delete) のタプル

        Raises:
            DigestError: ファイルフォーマットが不正な場合
            FileIOError: ファイル読み込みに失敗した場合
        """
        provisional_data = load_json(provisional_path)
        log_debug(
            f"{LOG_PREFIX_VALIDATE} provisional_data: is_valid={is_valid_dict(provisional_data)}"
        )

        if not is_valid_dict(provisional_data):
            formatter = get_error_formatter()
            raise DigestError(formatter.validation.invalid_type(provisional_path.name, "dict", provisional_data))

        individual_digests = provisional_data.get("individual_digests", [])
        log_debug(f"{LOG_PREFIX_STATE} loaded_digests_count: {len(individual_digests)}")
        log_info(
            f"Loaded {len(individual_digests)} individual digests from {provisional_path.name}"
        )

        return individual_digests, provisional_path

    def load_or_generate(
        self, level: str, shadow_digest: OverallDigestData, digest_num: str
    ) -> Tuple[List[IndividualDigestData], Optional[Path]]:
        """
        Provisionalの読み込みまたはソースから自動生成

        Args:
            level: ダイジェストレベル
            shadow_digest: Shadowダイジェストデータ
            digest_num: ダイジェスト番号（ゼロ埋め済み）

        Returns:
            (individual_digests, provisional_file_to_delete) のタプル

        Raises:
            DigestError: Provisionalファイルのフォーマットが不正な場合
            FileIOError: Provisionalファイルの読み込みに失敗した場合
        """
        provisional_path = self._get_provisional_path(level, digest_num)

        log_debug(f"{LOG_PREFIX_FILE} load_or_generate: checking {provisional_path}")
        log_debug(f"{LOG_PREFIX_FILE} file_exists: {provisional_path.exists()}")

        if provisional_path.exists():
            return self._load_provisional(provisional_path)

        # Provisionalファイルが存在しない場合、source_filesから自動生成
        log_debug(f"{LOG_PREFIX_DECISION} provisional_not_found: generating from source files")
        log_info("No Provisional digest found, generating from source files...")
        individual_digests = self.generate_from_source(level, shadow_digest)

        return individual_digests, None

    def _build_individual_entry(
        self, source_file: str, source_data: Dict[str, Any]
    ) -> IndividualDigestData:
        """
        ソースデータから個別ダイジェストエントリを構築

        Args:
            source_file: ソースファイル名
            source_data: ソースファイルから読み込んだJSONデータ

        Returns:
            個別ダイジェストエントリ
        """
        overall = source_data.get("overall_digest", {})
        return {
            "source_file": source_file,
            "digest_type": overall.get("digest_type", ""),
            "keywords": overall.get("keywords", []),
            "abstract": overall.get("abstract", ""),
            "impression": overall.get("impression", ""),
        }

    def generate_from_source(
        self, level: str, shadow_digest: OverallDigestData
    ) -> List[IndividualDigestData]:
        """
        ソースファイルからindividual_digestsを自動生成（まだらボケ回避）

        Args:
            level: ダイジェストレベル
            shadow_digest: Shadowダイジェストデータ

        Returns:
            individual_digestsのリスト
        """
        individual_digests: List[IndividualDigestData] = []
        source_files = shadow_digest.get("source_files", [])
        skipped_count = 0
        source_dir = self._get_source_path_for_level(level)

        log_debug(
            f"{LOG_PREFIX_STATE} generate_from_source: level={level}, source_count={len(source_files)}"
        )
        log_debug(f"{LOG_PREFIX_FILE} source_dir: {source_dir}")

        for source_file in source_files:
            source_path = source_dir / source_file
            log_debug(f"{LOG_PREFIX_FILE} processing: {source_path}")
            source_data = try_read_json_from_file(source_path)

            if source_data is None:
                log_debug(f"{LOG_PREFIX_FILE} skipped (read failed): {source_file}")
                skipped_count += 1
                continue

            individual_entry = self._build_individual_entry(source_file, source_data)
            individual_digests.append(individual_entry)
            log_info(f"Auto-generated individual digest from {source_file}")

        if skipped_count > 0:
            log_warning(f"Skipped {skipped_count}/{len(source_files)} files due to errors")
        log_info(f"Auto-generated {len(individual_digests)} individual digests from source files")
        return individual_digests
