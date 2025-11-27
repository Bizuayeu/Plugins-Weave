#!/usr/bin/env python3
"""
File Detector for Shadow Updates
================================

GrandDigest更新後に作成された新しいファイルを検出
"""

from pathlib import Path
from typing import List, Optional

from config import DigestConfig, LEVEL_CONFIG, extract_number_only
from application.tracking import DigestTimesTracker
from infrastructure import log_warning


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

        # レベル階層情報を構築
        self.level_hierarchy = {
            level: {"source": cfg["source"], "next": cfg["next"]}
            for level, cfg in LEVEL_CONFIG.items()
        }

    def get_max_file_number(self, level: str) -> Optional[str]:
        """
        指定レベルの最大ファイル番号を取得

        Args:
            level: レベル名

        Returns:
            最大ファイル番号（文字列）またはNone
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
        """
        source_type = self.level_hierarchy[level]["source"]

        if source_type == "loops":
            # Weekly: Loopファイルを参照
            return self.config.loops_path
        else:
            # Monthly以上: 下位レベルのDigestファイルを参照
            try:
                return self.config.get_level_dir(source_type)
            except ValueError:
                raise ValueError(f"Unknown source type: {source_type}")

    def find_new_files(self, level: str) -> List[Path]:
        """
        GrandDigest更新後に作成された新しいファイルを検出

        Args:
            level: レベル名

        Returns:
            新しいファイルのPathリスト
        """
        max_file_number = self.get_max_file_number(level)

        # ソースディレクトリとパターンを決定
        source_info = self.level_hierarchy[level]["source"]
        if source_info == "loops":
            source_dir = self.config.loops_path
            pattern = "Loop*.txt"
        else:
            source_dir = self.config.get_level_dir(source_info)
            pattern = f"{self.level_config[source_info]['prefix']}*.txt"

        if not source_dir.exists():
            return []

        # ファイルを検出
        all_files = sorted(source_dir.glob(pattern))

        if max_file_number is None:
            # 初回は全ファイルを検出
            return all_files

        # 最大番号より大きいファイルを抽出
        max_num = extract_number_only(max_file_number)

        # max_numがNoneの場合（max_file_numberが無効な場合）は全ファイルを返す
        if max_num is None:
            log_warning(f"Invalid max_file_number format: {max_file_number}, returning all files")
            return all_files

        new_files = []

        for file in all_files:
            file_num = extract_number_only(file.name)
            if file_num is not None and file_num > max_num:
                new_files.append(file)

        return new_files
