#!/usr/bin/env python3
"""
GrandDigest Manager
===================

GrandDigest.txt の管理を担当するモジュール。
finalize_from_shadow.py から分離。
"""
import json
from datetime import datetime
from typing import Dict, Any

from config import DigestConfig, LEVEL_NAMES
from digest_types import OverallDigestData, GrandDigestData
from utils import log_info, log_error, load_json_with_template, save_json
from __version__ import DIGEST_FORMAT_VERSION
from validators import is_valid_dict


class GrandDigestManager:
    """GrandDigest.txt管理クラス"""

    def __init__(self, config: DigestConfig):
        self.config = config
        self.grand_digest_file = config.essences_path / "GrandDigest.txt"

    def get_template(self) -> GrandDigestData:
        """GrandDigest.txtのテンプレートを返す（全8レベル対応）"""
        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": DIGEST_FORMAT_VERSION
            },
            "major_digests": {
                level: {"overall_digest": None}
                for level in LEVEL_NAMES
            }
        }

    def load_or_create(self) -> GrandDigestData:
        """GrandDigest.txtを読み込む。存在しなければテンプレートで作成"""
        return load_json_with_template(
            target_file=self.grand_digest_file,
            default_factory=self.get_template,
            log_message="GrandDigest.txt not found. Creating new file."
        )

    def save(self, data: GrandDigestData) -> None:
        """GrandDigest.txtを保存"""
        save_json(self.grand_digest_file, data)

    def update_digest(self, level: str, digest_name: str, overall_digest: OverallDigestData) -> bool:
        """指定レベルのダイジェストを更新"""
        grand_data = self.load_or_create()

        # 型チェック
        if not is_valid_dict(grand_data):
            log_error("GrandDigest.txt has invalid format: expected dict")
            return False

        if "major_digests" not in grand_data:
            log_error("GrandDigest.txt missing 'major_digests' section")
            return False

        if level not in grand_data["major_digests"]:
            log_error(f"Unknown level: {level}")
            return False

        # overall_digestを更新（完全なオブジェクトとして保存）
        grand_data["major_digests"][level]["overall_digest"] = overall_digest

        # メタデータを更新
        grand_data["metadata"]["last_updated"] = datetime.now().isoformat()

        # 保存
        self.save(grand_data)
        log_info(f"Updated GrandDigest.txt for level: {level}")
        return True
