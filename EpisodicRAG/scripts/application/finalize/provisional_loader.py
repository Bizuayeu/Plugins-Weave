#!/usr/bin/env python3
"""
Provisional Loader
==================

ProvisionalDigestの読み込みまたはソースファイルからの自動生成
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from config import DigestConfig, LEVEL_CONFIG
from application.validators import is_valid_dict
from domain.exceptions import DigestError, FileIOError
from infrastructure import log_info, log_warning
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

    def load_or_generate(
        self, level: str, shadow_digest: Dict[str, Any], digest_num: str
    ) -> Tuple[List[Dict[str, Any]], Optional[Path]]:
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

        individual_digests: List[Dict[str, Any]] = []
        provisional_file_to_delete: Optional[Path] = None

        if provisional_path.exists():
            try:
                with open(provisional_path, 'r', encoding='utf-8') as f:
                    provisional_data = json.load(f)
                    if not is_valid_dict(provisional_data):
                        raise DigestError(f"Invalid format in {provisional_path.name}: expected dict")
                    individual_digests = provisional_data.get("individual_digests", [])
                log_info(f"Loaded {len(individual_digests)} individual digests from {provisional_path.name}")
                provisional_file_to_delete = provisional_path
            except json.JSONDecodeError as e:
                raise FileIOError(f"Invalid JSON in {provisional_path.name}: {e}")
            except IOError as e:
                raise FileIOError(f"Failed to read {provisional_path}: {e}")
        else:
            # Provisionalファイルが存在しない場合、source_filesから自動生成
            log_info("No Provisional digest found, generating from source files...")
            individual_digests = self.generate_from_source(level, shadow_digest)

        return individual_digests, provisional_file_to_delete

    def generate_from_source(
        self, level: str, shadow_digest: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        ソースファイルからindividual_digestsを自動生成（まだらボケ回避）

        Args:
            level: ダイジェストレベル
            shadow_digest: Shadowダイジェストデータ

        Returns:
            individual_digestsのリスト
        """
        individual_digests: List[Dict[str, Any]] = []
        source_files = shadow_digest.get("source_files", [])

        for source_file in source_files:
            try:
                source_dir = self.shadow_manager._get_source_path(level)
                source_path = source_dir / source_file

                if source_path.exists() and source_path.suffix == '.txt':
                    with open(source_path, 'r', encoding='utf-8') as f:
                        source_data = json.load(f)
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
            except json.JSONDecodeError:
                log_warning(f"Failed to parse {source_file} as JSON")
            except OSError as e:
                log_warning(f"Error reading {source_file}: {e}")

        log_info(f"Auto-generated {len(individual_digests)} individual digests from source files")
        return individual_digests
