#!/usr/bin/env python3
"""
Shadow Updater
==============

ShadowGrandDigestの更新、カスケード処理を担当（Facade）
"""

from pathlib import Path
from typing import Dict, List, Optional

from domain.types import LevelHierarchyEntry, OverallDigestData
from infrastructure import get_structured_logger

from .cascade_processor import CascadeProcessor
from .file_appender import FileAppender
from .file_detector import FileDetector
from .placeholder_manager import PlaceholderManager
from .shadow_io import ShadowIO
from .template import ShadowTemplate

_logger = get_structured_logger(__name__)


class ShadowUpdater:
    """
    ShadowGrandDigest更新クラス（Facade）

    このクラスはFacadeパターンを採用し、複数の内部コンポーネント
    （FileAppender, CascadeProcessor, PlaceholderManager）を統合して
    シンプルなAPIを提供します。

    Design Pattern: Facade
        複雑なサブシステムをシンプルなインターフェースで隠蔽。

    Learning Point:
        呼び出し側は内部コンポーネントの存在を意識せずにShadow操作が可能。
        内部実装の変更が外部APIに影響しないため、保守性が向上。

    設計意図:
    - 呼び出し側は内部コンポーネントの存在を意識せずにShadow操作が可能
    - 内部コンポーネントの変更が外部に影響しない（カプセル化）
    - テスト時はこのクラスをモックするだけで済む

    内部コンポーネント:
    - FileAppender: ファイル追加処理
    - CascadeProcessor: カスケード処理（階層間の連携）
    - PlaceholderManager: プレースホルダー管理
    """

    def __init__(
        self,
        shadow_io: ShadowIO,
        file_detector: FileDetector,
        template: ShadowTemplate,
        level_hierarchy: Dict[str, LevelHierarchyEntry],
    ):
        """
        初期化

        Args:
            shadow_io: ShadowIO インスタンス
            file_detector: FileDetector インスタンス
            template: ShadowTemplate インスタンス
            level_hierarchy: レベル階層情報
        """
        self.shadow_io = shadow_io
        self.file_detector = file_detector
        self.template = template
        self.level_hierarchy = level_hierarchy

        # 内部コンポーネントを初期化
        self._placeholder_manager = PlaceholderManager()
        self._file_appender = FileAppender(
            shadow_io, file_detector, template, level_hierarchy, self._placeholder_manager
        )
        self._cascade_processor = CascadeProcessor(
            shadow_io, file_detector, template, level_hierarchy, self._file_appender
        )

    # =========================================================================
    # パブリックメソッド委譲
    # =========================================================================

    def add_files_to_shadow(self, level: str, new_files: List[Path]) -> None:
        """
        指定レベルのShadowに新しいファイルを追加（増分更新）

        Args:
            level: 対象レベル（"weekly", "monthly"等）
            new_files: 追加するファイルパスのリスト

        Note:
            - ファイルはsource_filesに追加される
            - overall_digestが未初期化の場合は自動的に初期化
            - プレースホルダーが設定され、Claude分析待ちとなる

        Example:
            >>> updater = ShadowUpdater(shadow_io, file_detector, template, hierarchy)
            >>> new_files = [Path("Loops/L00186_test.txt"), Path("Loops/L00187_test.txt")]
            >>> updater.add_files_to_shadow("weekly", new_files)
            # shadow["weekly"]["source_files"] に "L00186_test.txt", "L00187_test.txt" が追加される
        """
        return self._file_appender.add_files_to_shadow(level, new_files)

    def clear_shadow_level(self, level: str) -> None:
        """
        指定レベルのShadowを初期化

        Args:
            level: 対象レベル（"weekly", "monthly"等）

        Note:
            ダイジェスト確定後にShadowをクリアする際に使用。
            source_files、overall_digestをテンプレート状態にリセット。
        """
        return self._cascade_processor.clear_shadow_level(level)

    def get_shadow_digest_for_level(self, level: str) -> Optional[OverallDigestData]:
        """
        指定レベルのShadowダイジェストを取得

        Args:
            level: 対象レベル（"weekly", "monthly"等）

        Returns:
            OverallDigestData: Shadowダイジェストデータ
            None: レベルにデータが存在しない場合
        """
        return self._cascade_processor.get_shadow_digest_for_level(level)

    def promote_shadow_to_grand(self, level: str) -> None:
        """
        ShadowのレベルをGrandDigestに昇格

        Args:
            level: 対象レベル（"weekly", "monthly"等）

        Note:
            GrandDigest.txtの該当レベルにShadowの内容をコピー。
            通常は finalize_from_shadow.py から呼び出される。
        """
        return self._cascade_processor.promote_shadow_to_grand(level)

    def update_shadow_for_new_loops(self) -> None:
        """
        新しいLoopファイルを検出してShadowを増分更新

        last_digest_times.json を参照し、前回処理以降の新規Loopファイルを
        検出してweekly Shadowに追加する。

        Note:
            - 新規ファイルがない場合は何も行わない
            - Shadowファイルが存在しない場合は自動作成
            - 追加後、Claude分析待ちのプレースホルダーが設定される
        """
        # Shadowファイルを読み込み（存在しなければ作成）
        self.shadow_io.load_or_create()

        new_files = self.file_detector.find_new_files("weekly")

        if not new_files:
            _logger.info("新規Loopファイルなし")
            return

        _logger.info(f"新規Loopファイル {len(new_files)}件検出:")

        # Shadowに増分追加
        self.add_files_to_shadow("weekly", new_files)

    def cascade_update_on_digest_finalize(self, level: str) -> None:
        """
        ダイジェスト確定時のカスケード処理

        指定レベルのダイジェストが確定した際に、上位レベルのShadowを更新する。
        例: weekly確定時 → monthly Shadowに新しいweeklyダイジェストを追加

        Args:
            level: 確定したレベル（"weekly", "monthly"等）

        Note:
            - 確定レベルのShadowはクリアされる
            - 上位レベルのShadowに新しいソースファイルが追加される
            - 8階層カスケード構造に従って処理が連鎖

        Example:
            >>> updater = ShadowUpdater(shadow_io, file_detector, template, hierarchy)
            >>> updater.cascade_update_on_digest_finalize("weekly")
            # weekly Shadowがクリアされ、W0042.txt が monthly Shadow に追加される
        """
        return self._cascade_processor.cascade_update_on_digest_finalize(level)
