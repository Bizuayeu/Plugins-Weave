#!/usr/bin/env python3
"""
Provisional Loader
==================

ProvisionalDigestの読み込みまたはソースファイルからの自動生成
"""

from pathlib import Path
from typing import Optional, Tuple, List

from config import DigestConfig, LEVEL_CONFIG
from application.validators import is_valid_dict
from domain.types import OverallDigestData, IndividualDigestData
from domain.exceptions import DigestError, FileIOError
from infrastructure import log_info, log_warning, load_json, read_json_from_file_safe
from application.grand import ShadowGrandDigestManager


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
        level_cfg = self.level_config[level]
        provisional_dir = self.config.get_provisional_dir(level)
        provisional_path = provisional_dir / f"{level_cfg['prefix']}{digest_num}_Individual.txt"

        individual_digests: List[IndividualDigestData] = []
        provisional_file_to_delete: Optional[Path] = None

        if provisional_path.exists():
            provisional_data = load_json(provisional_path)
            if not is_valid_dict(provisional_data):
                raise DigestError(f"Invalid format in {provisional_path.name}: expected dict")
            individual_digests = provisional_data.get("individual_digests", [])
            log_info(f"Loaded {len(individual_digests)} individual digests from {provisional_path.name}")
            provisional_file_to_delete = provisional_path
        else:
            # Provisionalファイルが存在しない場合、source_filesから自動生成
            log_info("No Provisional digest found, generating from source files...")
            individual_digests = self.generate_from_source(level, shadow_digest)

        return individual_digests, provisional_file_to_delete

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

        for source_file in source_files:
            source_dir = self._get_source_path_for_level(level)
            source_path = source_dir / source_file

            source_data = read_json_from_file_safe(source_path)
            if source_data is None:
                skipped_count += 1
                continue

            overall = source_data.get("overall_digest", {})
            individual_entry = {
                "filename": source_file,
                "timestamp": overall.get("timestamp", ""),
                "digest_type": overall.get("digest_type", ""),
                "keywords": overall.get("keywords", []),
                "abstract": overall.get("abstract", ""),
                "impression": overall.get("impression", "")
            }
            individual_digests.append(individual_entry)
            log_info(f"Auto-generated individual digest from {source_file}")

        if skipped_count > 0:
            log_warning(f"Skipped {skipped_count}/{len(source_files)} files due to errors")
        log_info(f"Auto-generated {len(individual_digests)} individual digests from source files")
        return individual_digests
