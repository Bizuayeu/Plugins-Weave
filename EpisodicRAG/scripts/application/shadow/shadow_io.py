#!/usr/bin/env python3
"""
Shadow I/O Handler
==================

ShadowGrandDigest.txtの読み書きを担当
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Callable

from infrastructure import load_json_with_template, save_json


class ShadowIO:
    """ShadowGrandDigest I/Oクラス"""

    def __init__(self, shadow_digest_file: Path, template_factory: Callable[[], Dict[str, Any]]):
        """
        初期化

        Args:
            shadow_digest_file: ShadowGrandDigest.txtのパス
            template_factory: テンプレートを返す関数（遅延評価用）
        """
        self.shadow_digest_file = shadow_digest_file
        self.template_factory = template_factory

    def load_or_create(self) -> Dict[str, Any]:
        """
        ShadowGrandDigestを読み込む。存在しなければ作成

        Returns:
            ShadowGrandDigestのデータ構造
        """
        return load_json_with_template(
            target_file=self.shadow_digest_file,
            default_factory=self.template_factory,
            log_message="ShadowGrandDigest.txt not found. Creating new file."
        )

    def save(self, data: Dict[str, Any]) -> None:
        """
        ShadowGrandDigestを保存

        Args:
            data: 保存するデータ
        """
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        save_json(self.shadow_digest_file, data)
