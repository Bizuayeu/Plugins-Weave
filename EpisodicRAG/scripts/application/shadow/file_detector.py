#!/usr/bin/env python3
"""
File Detector for Shadow Updates
================================

GrandDigest更新後に作成された新しいファイルを検出
"""

from pathlib import Path
from typing import List, Optional

from application.config import DigestConfig
from application.tracking import DigestTimesTracker
from domain.constants import LEVEL_CONFIG, SOURCE_TYPE_LOOPS, SOURCE_TYPE_RAW, build_level_hierarchy
from domain.file_naming import filter_files_after
from infrastructure import get_structured_logger

# 構造化ロガー
_logger = get_structured_logger(__name__)


class FileDetector:
    """新規ファイル検出クラス"""

    def __init__(self, config: DigestConfig, times_tracker: DigestTimesTracker):
        """
        初期化

        Args:
            config: DigestConfig インスタンス
            times_tracker: DigestTimesTracker インスタンス
        """
        self.config = config
        self.times_tracker = times_tracker
        self.level_config = LEVEL_CONFIG

        # レベル階層情報を構築（SSoT関数を使用）
        self.level_hierarchy = build_level_hierarchy()

    def _get_detection_level(self, level: str) -> str:
        """
        検出に使用するレベル（ソースレベル）を返す

        新規ファイル検出時、そのレベルのソースファイルの last_processed を参照する。
        例: monthly の新規ファイル検出には weekly.last_processed を使用

        Args:
            level: ダイジェストレベル

        Returns:
            検出に使用するソースレベル名

        Example:
            >>> detector._get_detection_level("weekly")
            "loop"
            >>> detector._get_detection_level("monthly")
            "weekly"
            >>> detector._get_detection_level("quarterly")
            "monthly"
        """
        source = self.level_config[level].get("source")

        # source が "loops" の場合は "loop" を返す
        if source == SOURCE_TYPE_LOOPS:
            return "loop"

        # source が "raw" の場合（loopレベル）は自身を返す
        if source == SOURCE_TYPE_RAW:
            return level

        # それ以外はソースレベル名をそのまま返す
        # sourceがNoneの場合は自身のレベルを返す（フォールバック）
        return source if source is not None else level

    def get_max_file_number(self, level: str) -> Optional[int]:
        """
        指定レベルの最大ファイル番号を取得

        Args:
            level: レベル名

        Returns:
            最大ファイル番号（整数）またはNone

        Example:
            >>> detector = FileDetector(config, times_tracker)
            >>> detector.get_max_file_number("weekly")
            42
        """
        times_data = self.times_tracker.load_or_create()
        level_data = times_data.get(level, {})
        return level_data.get("last_processed")

    def get_source_path(self, level: str) -> Path:
        """
        指定レベルのソースファイルが格納されているディレクトリを返す

        Args:
            level: "weekly", "monthly", "quarterly"など

        Returns:
            Path: ソースファイルのディレクトリ

        Raises:
            ValueError: 不明なソースタイプの場合

        Example:
            >>> detector.get_source_path("weekly")
            Path('/project/Loops')
            >>> detector.get_source_path("monthly")
            Path('/project/Digests/1_Weekly')
        """
        # 統一メソッドを使用
        return self.config.get_source_dir(level)

    def find_new_files(self, level: str) -> List[Path]:
        """
        GrandDigest更新後に作成された新しいファイルを検出

        Args:
            level: レベル名

        Returns:
            新しいファイルのPathリスト

        Example:
            >>> detector = FileDetector(config, times_tracker)
            >>> new_files = detector.find_new_files("weekly")
            >>> [f.name for f in new_files]
            ['L00186_test.txt', 'L00187_test.txt']
        """
        _logger.state("find_new_files", level=level)

        # 検出に使用するレベルを取得（weeklyはloopを参照）
        detection_level = self._get_detection_level(level)
        max_file_number = self.get_max_file_number(detection_level)

        _logger.decision(
            "detection_criteria",
            detection_level=detection_level,
            max_num=max_file_number,
        )

        # 統一メソッドを使用してソースディレクトリとパターンを取得
        source_dir = self.config.get_source_dir(level)
        pattern = self.config.get_source_pattern(level)

        if not source_dir.exists():
            _logger.file_op("found", count=0, reason="source_dir_not_exists")
            return []

        # ファイルを検出
        all_files = sorted(source_dir.glob(pattern))

        if max_file_number is None:
            # 初回は全ファイルを検出
            _logger.file_op("found", count=len(all_files), filter="none_initial")
            return all_files

        # 統一関数を使用してフィルタリング
        result = filter_files_after(all_files, max_file_number)
        _logger.file_op("found", count=len(result), filtered_from=len(all_files))
        return result
