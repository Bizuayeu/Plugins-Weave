#!/usr/bin/env python3
"""
Shadow I/O Handler
==================

ShadowGrandDigest.txt のファイルI/O操作を担当するアプリケーション層モジュール。

ShadowGrandDigest.txt は作業中のダイジェスト情報を保持する一時ファイル。
各階層レベルの「まだ確定されていない」ダイジェスト情報を管理し、
finalize時にGrandDigest.txtへ昇格される。

Usage:
    from application.shadow import ShadowIO, ShadowTemplate
    from application.config import DigestConfig

    config = DigestConfig()
    template = ShadowTemplate()

    shadow_io = ShadowIO(
        shadow_digest_file=config.essences_path / "ShadowGrandDigest.txt",
        template_factory=template.create_shadow_template
    )

    # 読み込み（存在しなければ自動作成）
    data = shadow_io.load_or_create()

    # 保存（タイムスタンプ自動更新）
    shadow_io.save(data)

Design Pattern:
    - Repository Pattern: ファイルI/Oの抽象化
    - Factory Pattern: テンプレート生成の遅延評価

Related Modules:
    - application.shadow.shadow_updater: Shadowの更新ロジック
    - application.shadow.template: テンプレート生成
    - infrastructure.json_repository: JSON I/O操作

Note:
    テンプレート生成は template_factory 経由で遅延評価される。
    これにより循環参照を回避しつつ、必要時にのみテンプレートを生成。
"""

from datetime import datetime
from pathlib import Path
from typing import Callable

from domain.constants import LOG_PREFIX_FILE, LOG_PREFIX_STATE, LOG_PREFIX_VALIDATE
from domain.types import ShadowDigestData, as_dict
from infrastructure import load_json_with_template, log_debug, save_json


class ShadowIO:
    """
    ShadowGrandDigest.txt の読み込み・保存を担当するI/Oクラス。

    このクラスはRepository Patternを採用し、ShadowGrandDigest.txtへの
    すべてのファイルI/O操作を一元管理する。

    Attributes:
        shadow_digest_file: ShadowGrandDigest.txt のパス
        template_factory: テンプレート生成関数（遅延評価用）

    Example:
        >>> shadow_io = ShadowIO(path, template_factory)
        >>> data = shadow_io.load_or_create()
        >>> data["latest_digests"]["weekly"]["source_files"].append("new_file.txt")
        >>> shadow_io.save(data)

    Note:
        save()時にmetadata.last_updatedが自動更新される。
    """

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

        Example:
            >>> shadow_io = ShadowIO(Path("ShadowGrandDigest.txt"), template_factory)
            >>> data = shadow_io.load_or_create()
            >>> list(data["latest_digests"].keys())
            ['weekly', 'monthly', 'quarterly', ...]
        """
        log_debug(f"{LOG_PREFIX_FILE} load_or_create: {self.shadow_digest_file}")
        log_debug(f"{LOG_PREFIX_FILE} file_exists: {self.shadow_digest_file.exists()}")

        result = load_json_with_template(
            target_file=self.shadow_digest_file,
            default_factory=self.template_factory,
            log_message="ShadowGrandDigest.txt not found. Creating new file.",
        )

        log_debug(f"{LOG_PREFIX_VALIDATE} loaded_data: keys={list(result.keys())}")
        return result

    def save(self, data: ShadowDigestData) -> None:
        """
        ShadowGrandDigestを保存

        Args:
            data: 保存するデータ
        """
        log_debug(f"{LOG_PREFIX_FILE} save: {self.shadow_digest_file}")
        log_debug(f"{LOG_PREFIX_VALIDATE} data_keys: {list(data.keys())}")

        data["metadata"]["last_updated"] = datetime.now().isoformat()
        log_debug(f"{LOG_PREFIX_STATE} updated_timestamp: {data['metadata']['last_updated']}")

        # Cast TypedDict to Dict for infrastructure compatibility
        save_json(self.shadow_digest_file, as_dict(data))
