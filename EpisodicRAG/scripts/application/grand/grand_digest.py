#!/usr/bin/env python3
"""
GrandDigest Manager
===================

GrandDigest.txt の管理を担当するモジュール。
finalize_from_shadow.py から分離。
"""

from datetime import datetime
from typing import Any, Callable, Dict, cast

from application.validators import is_valid_dict
from config import DigestConfig
from domain.constants import LEVEL_NAMES
from domain.exceptions import DigestError
from domain.types import GrandDigestData, OverallDigestData
from domain.version import DIGEST_FORMAT_VERSION
from infrastructure import load_json_with_template, log_info, save_json


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
                "version": DIGEST_FORMAT_VERSION,
            },
            "major_digests": {level: {"overall_digest": None} for level in LEVEL_NAMES},
        }

    def load_or_create(self) -> GrandDigestData:
        """GrandDigest.txtを読み込む。存在しなければテンプレートで作成"""
        # Cast factory for infrastructure compatibility
        factory = cast(Callable[[], Dict[str, Any]], self.get_template)
        result = load_json_with_template(
            target_file=self.grand_digest_file,
            default_factory=factory,
            log_message="GrandDigest.txt not found. Creating new file.",
        )
        return cast(GrandDigestData, result)

    def save(self, data: GrandDigestData) -> None:
        """GrandDigest.txtを保存"""
        save_json(self.grand_digest_file, cast(Dict[str, Any], data))

    def update_digest(
        self, level: str, digest_name: str, overall_digest: OverallDigestData
    ) -> None:
        """
        指定レベルのダイジェストを更新

        Args:
            level: ダイジェストレベル
            digest_name: ダイジェスト名
            overall_digest: overall_digestデータ

        Raises:
            DigestError: GrandDigest.txtのフォーマットが不正、またはレベルが無効な場合
        """
        grand_data = self.load_or_create()

        # 型チェック
        if not is_valid_dict(grand_data):
            raise DigestError("GrandDigest.txt has invalid format: expected dict")

        if "major_digests" not in grand_data:
            raise DigestError("GrandDigest.txt missing 'major_digests' section")

        if level not in grand_data["major_digests"]:
            raise DigestError(f"Unknown level: {level}")

        # overall_digestを更新（完全なオブジェクトとして保存）
        grand_data["major_digests"][level]["overall_digest"] = overall_digest

        # メタデータを更新
        grand_data["metadata"]["last_updated"] = datetime.now().isoformat()

        # 保存
        self.save(grand_data)
        log_info(f"Updated GrandDigest.txt for level: {level}")
