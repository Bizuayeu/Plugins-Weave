#!/usr/bin/env python3
"""
GrandDigest Manager
===================

GrandDigest.txt の管理を担当するアプリケーション層モジュール。

GrandDigest.txtは全8階層のダイジェスト要約を統合する最上位ファイル。
各階層（Weekly〜Centurial）のoverall_digestを保持し、
長期記憶の集約ポイントとして機能する。

Usage:
    from application.grand import GrandDigestManager
    from application.config import DigestConfig

    config = DigestConfig()
    manager = GrandDigestManager(config)

    # 読み込み（存在しなければ自動作成）
    data = manager.load_or_create()

    # 特定レベルの更新
    manager.update_digest("weekly", "W0001", overall_digest_data)

Design Pattern:
    - Repository Pattern: ファイルI/Oを抽象化
    - Template Method: テンプレート生成の標準化

Related Modules:
    - application.grand.shadow_grand_digest: Shadow版の管理
    - infrastructure.json_repository: JSON I/O操作
    - domain.types: GrandDigestData型定義

Note:
    finalize_from_shadow.py から分離された管理クラス。
    ファイル構造の詳細は docs/dev/ARCHITECTURE.md を参照。
"""

from datetime import datetime
from typing import cast

from application.config import DigestConfig
from domain.constants import (
    LEVEL_NAMES,
    LOG_PREFIX_STATE,
    LOG_PREFIX_VALIDATE,
)
from domain.file_constants import GRAND_DIGEST_FILENAME
from domain.error_formatter import get_error_formatter
from domain.exceptions import DigestError
from domain.types import GrandDigestData, OverallDigestData, as_dict
from domain.validators import is_valid_dict
from domain.version import DIGEST_FORMAT_VERSION
from infrastructure import get_structured_logger, load_json_with_template, log_debug, save_json

_logger = get_structured_logger(__name__)


class GrandDigestManager:
    """
    GrandDigest.txt の読み込み・保存・更新を担当する管理クラス。

    このクラスはRepository Patternを採用し、GrandDigest.txtへの
    すべてのファイルI/O操作を一元管理する。

    Attributes:
        config: DigestConfig インスタンス
        grand_digest_file: GrandDigest.txt のパス

    Example:
        >>> from application.grand import GrandDigestManager
        >>> from application.config import DigestConfig
        >>> manager = GrandDigestManager(DigestConfig())
        >>> data = manager.load_or_create()
        >>> manager.update_digest("weekly", "W0001", overall_digest)

    Note:
        GrandDigest.txtが存在しない場合、get_template()で
        自動的にテンプレートが作成される。
    """

    def __init__(self, config: DigestConfig):
        self.config = config
        self.grand_digest_file = config.essences_path / GRAND_DIGEST_FILENAME

    def get_template(self) -> GrandDigestData:
        """
        GrandDigest.txtのテンプレートを返す（全8レベル対応）

        Returns:
            GrandDigestData: 以下の構造を持つ辞書
                - metadata: {last_updated: str, version: str}
                - major_digests: {level: {overall_digest: None}, ...}
        """
        return {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "version": DIGEST_FORMAT_VERSION,
            },
            "major_digests": {level: {"overall_digest": None} for level in LEVEL_NAMES},
        }

    def load_or_create(self) -> GrandDigestData:
        """
        GrandDigest.txtを読み込む。存在しなければテンプレートで作成

        Returns:
            GrandDigestData: 読み込んだまたは新規作成したデータ

        Raises:
            FileIOError: ファイルの読み書きに失敗した場合
        """
        return load_json_with_template(
            target_file=self.grand_digest_file,
            default_factory=self.get_template,
            log_message="GrandDigest.txt not found. Creating new file.",
        )

    def save(self, data: GrandDigestData) -> None:
        """
        GrandDigest.txtを保存

        Args:
            data: 保存するGrandDigestデータ

        Raises:
            FileIOError: ファイル書き込みに失敗した場合
        """
        save_json(self.grand_digest_file, as_dict(data))

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

        log_debug(f"{LOG_PREFIX_STATE} update_digest: level={level}, digest_name={digest_name}")
        log_debug(f"{LOG_PREFIX_VALIDATE} grand_data: is_valid={is_valid_dict(grand_data)}")

        formatter = get_error_formatter()
        # 型チェック
        if not is_valid_dict(grand_data):
            raise DigestError(
                formatter.validation.invalid_type("GrandDigest.txt", "dict", grand_data)
            )

        if "major_digests" not in grand_data:
            raise DigestError(formatter.config.config_section_missing("major_digests"))

        available_levels = list(grand_data["major_digests"].keys())
        log_debug(f"{LOG_PREFIX_VALIDATE} available_levels: {available_levels}")

        if level not in grand_data["major_digests"]:
            raise DigestError(formatter.config.unknown_level(level))

        # overall_digestを更新（完全なオブジェクトとして保存）
        log_debug(f"{LOG_PREFIX_STATE} updating overall_digest for level={level}")
        log_debug(f"{LOG_PREFIX_VALIDATE} overall_digest_keys: {list(overall_digest.keys())}")
        grand_data["major_digests"][level]["overall_digest"] = overall_digest

        # メタデータを更新
        grand_data["metadata"]["last_updated"] = datetime.now().isoformat()
        log_debug(f"{LOG_PREFIX_STATE} updated_timestamp: {grand_data['metadata']['last_updated']}")

        # 保存
        self.save(cast(GrandDigestData, grand_data))
        _logger.info(f"Updated GrandDigest.txt for level: {level}")
