#!/usr/bin/env python3
"""
Shadow I/O Handler
==================

ShadowGrandDigest.txtの読み書きを担当
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, cast

from domain.types import ShadowDigestData, as_dict
from infrastructure import load_json_with_template, save_json


class ShadowIO:
    """ShadowGrandDigest I/Oクラス"""

    def __init__(self, shadow_digest_file: Path, template_factory: Callable[[], ShadowDigestData]):
        """
        初期化

        Args:
            shadow_digest_file: ShadowGrandDigest.txtのパス
            template_factory: テンプレートを返す関数（遅延評価用）
        """
        self.shadow_digest_file = shadow_digest_file
        self.template_factory = template_factory

    def load_or_create(self) -> ShadowDigestData:
        """
        ShadowGrandDigestを読み込む。存在しなければ作成

        Returns:
            ShadowGrandDigestのデータ構造
        """
        # Cast factory to Dict[str, Any] for infrastructure compatibility
        factory = cast(Callable[[], Dict[str, Any]], self.template_factory)
        result = load_json_with_template(
            target_file=self.shadow_digest_file,
            default_factory=factory,
            log_message="ShadowGrandDigest.txt not found. Creating new file.",
        )
        return cast(ShadowDigestData, result)

    def save(self, data: ShadowDigestData) -> None:
        """
        ShadowGrandDigestを保存

        Args:
            data: 保存するデータ
        """
        data["metadata"]["last_updated"] = datetime.now().isoformat()
        # Cast TypedDict to Dict for infrastructure compatibility
        save_json(self.shadow_digest_file, as_dict(data))
