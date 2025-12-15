#!/usr/bin/env python3
"""
Digest Times Tracker
====================

last_digest_times.json の管理を担当するモジュール。
finalize_from_shadow.py から分離。
"""

from datetime import datetime
from typing import List, Optional, Union, cast

from application.config import DigestConfig
from domain.constants import LEVEL_NAMES
from domain.file_constants import DIGEST_TIMES_FILENAME, DIGEST_TIMES_TEMPLATE
from domain.file_naming import extract_number_only, extract_numbers_formatted
from domain.types import DigestTimesData
from domain.validators import is_valid_list
from infrastructure import get_structured_logger, load_json_with_template, log_warning, save_json
from infrastructure.config import get_persistent_config_dir
from infrastructure.config.persistent_path import get_template_dir

_logger = get_structured_logger(__name__)


class DigestTimesTracker:
    """last_digest_times.json 管理クラス"""

    def __init__(self, config: DigestConfig):
        self.config = config
        # 永続化ディレクトリに保存（auto-update対象外）
        self.last_digest_file = get_persistent_config_dir() / DIGEST_TIMES_FILENAME
        # テンプレートは.claude-plugin/ディレクトリから取得
        template_dir = get_template_dir()
        self.template_file = template_dir / DIGEST_TIMES_TEMPLATE if template_dir else None

    def _get_default_template(self) -> DigestTimesData:
        """テンプレートがない場合のデフォルト構造を返す"""
        return {level: {"timestamp": "", "last_processed": None} for level in LEVEL_NAMES}

    def load_or_create(self) -> DigestTimesData:
        """
        最終ダイジェスト生成時刻を読み込む（存在しなければテンプレートから初期化）

        Example:
            >>> tracker = DigestTimesTracker(config)
            >>> data = tracker.load_or_create()
            >>> "weekly" in data
            True
        """
        return load_json_with_template(
            target_file=self.last_digest_file,
            template_file=self.template_file,
            default_factory=self._get_default_template,
            log_message="Initialized last_digest_times.json from template",
        )

    def extract_file_numbers(self, level: str, input_files: Optional[List[str]]) -> List[str]:
        """
        ファイル名から連番を抽出（プレフィックス付き、ゼロ埋め維持）

        Args:
            level: ダイジェストレベル（将来の拡張用）
            input_files: ファイル名のリスト

        Returns:
            抽出・フォーマットされた連番リスト（無効な入力は空リスト）

        Example:
            >>> tracker.extract_file_numbers("weekly", ["L00186.txt", "L00187.txt"])
            ['L00186', 'L00187']
        """
        # 早期リターン: None、空、または無効な型
        if not input_files or not is_valid_list(input_files):
            if input_files is not None and not is_valid_list(input_files):
                log_warning(f"input_files is not a list: {type(input_files).__name__}")
            return []

        # Cast to satisfy List[Union[str, None]] signature (List invariance)
        files_with_optional = cast(List[Union[str, None]], input_files)
        return extract_numbers_formatted(files_with_optional)

    def _extract_last_processed(self, file_numbers: List[str]) -> Optional[int]:
        """
        ファイル番号リストから最後の番号を抽出

        Args:
            file_numbers: フォーマット済みファイル番号リスト（例: ["Loop0001", "Loop0005"]）

        Returns:
            最後のファイル番号（int）、またはリストが空ならNone
        """
        if not file_numbers:
            return None

        last_file_str = file_numbers[-1]
        return extract_number_only(last_file_str)

    def _save_level_data(self, level: str, last_processed: Optional[int]) -> None:
        """
        共通保存ロジック（内部用）

        Args:
            level: ダイジェストレベル
            last_processed: 最後に処理した番号（Noneも許容）
        """
        times = self.load_or_create()
        times[level] = {
            "timestamp": datetime.now().isoformat(),
            "last_processed": last_processed,
        }
        save_json(self.last_digest_file, times)

    def save(self, level: str, input_files: Optional[List[str]] = None) -> None:
        """
        最終ダイジェスト生成時刻と最新処理済みファイル番号を保存

        Args:
            level: ダイジェストレベル
            input_files: 処理したファイル名のリスト（オプション）

        Example:
            >>> tracker = DigestTimesTracker(config)
            >>> tracker.save("weekly", ["L00186.txt", "L00187.txt"])
            # last_digest_times.json が更新される
        """
        # 空リスト警告
        if input_files is not None and len(input_files) == 0:
            log_warning(f"入力ファイルリストが空です: レベル {level}")

        # 連番抽出と最終番号取得
        file_numbers = self.extract_file_numbers(level, input_files or [])
        last_processed = self._extract_last_processed(file_numbers)

        # 共通ロジックで保存
        self._save_level_data(level, last_processed)

        _logger.info(f"last_digest_times.json更新完了: レベル {level}")
        if last_processed:
            _logger.info(f"最終処理番号: {last_processed}")

    def update_direct(self, level: str, last_processed: int) -> None:
        """
        last_processedを直接設定（CLIから呼び出し用）

        現在のsave()はファイル名リストから番号を抽出するが、
        CLIからは番号を直接指定したいケースがある。

        Args:
            level: ダイジェストレベル（loop, weekly等）
            last_processed: 設定する番号

        Example:
            >>> tracker = DigestTimesTracker(config)
            >>> tracker.update_direct("loop", 259)
            # last_digest_times.json の loop.last_processed が 259 に更新される
        """
        # 共通ロジックで保存
        self._save_level_data(level, last_processed)
        _logger.info(f"last_digest_times.json更新: {level} = {last_processed}")

    def save_digest_number(self, level: str, digest_number: int) -> None:
        """
        ダイジェスト番号を直接保存（確定時用）

        finalize_from_shadow時、source_filesの番号ではなく
        確定したダイジェスト番号を保存するために使用。

        Args:
            level: ダイジェストレベル（weekly, monthly等）
            digest_number: 確定したダイジェスト番号

        Example:
            >>> tracker = DigestTimesTracker(config)
            >>> tracker.save_digest_number("weekly", 52)
            # last_digest_times.json の weekly.last_processed が 52 に更新される
        """
        self._save_level_data(level, digest_number)
        _logger.info(f"last_digest_times.json更新（確定）: {level} = {digest_number}")
