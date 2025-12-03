#!/usr/bin/env python3
"""
Digest Persistence
==================

RegularDigestの保存、GrandDigest更新、カスケード処理を担当
"""

from pathlib import Path
from typing import Callable, List, Optional, cast

from application.config import DigestConfig
from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.tracking import DigestTimesTracker
from domain.constants import (
    LEVEL_CONFIG,
    LOG_PREFIX_DECISION,
    LOG_PREFIX_FILE,
    LOG_PREFIX_STATE,
)
from domain.error_formatter import get_error_formatter
from domain.exceptions import DigestError, FileIOError, ValidationError
from domain.level_registry import get_level_registry
from domain.types import OverallDigestData, RegularDigestData, as_dict
from domain.validators import is_valid_dict
from infrastructure import (
    get_default_confirm_callback,
    get_structured_logger,
    log_debug,
    log_warning,
    save_json,
)

_logger = get_structured_logger(__name__)


class DigestPersistence:
    """ダイジェストの永続化処理を担当"""

    def __init__(
        self,
        config: DigestConfig,
        grand_digest_manager: GrandDigestManager,
        shadow_manager: ShadowGrandDigestManager,
        times_tracker: DigestTimesTracker,
        confirm_callback: Optional[Callable[[str], bool]] = None,
    ):
        """
        Args:
            config: DigestConfig インスタンス
            grand_digest_manager: GrandDigestManager インスタンス
            shadow_manager: ShadowGrandDigestManager インスタンス
            times_tracker: DigestTimesTracker インスタンス
            confirm_callback: 確認コールバック関数（テスト用にモック可能）
        """
        self.config = config
        self.digests_path = config.digests_path
        self.grand_digest_manager = grand_digest_manager
        self.shadow_manager = shadow_manager
        self.times_tracker = times_tracker
        self.level_config = LEVEL_CONFIG
        self.confirm_callback = confirm_callback or get_default_confirm_callback()

    def save_regular_digest(
        self, level: str, regular_digest: RegularDigestData, new_digest_name: str
    ) -> Path:
        """
        RegularDigestをファイルに保存

        Args:
            level: ダイジェストレベル
            regular_digest: RegularDigest構造体
            new_digest_name: 新しいダイジェスト名

        Returns:
            保存先のPath

        Raises:
            FileIOError: ファイルの保存に失敗した場合
            ValidationError: ユーザーが上書きをキャンセルした場合

        Example:
            >>> persistence = DigestPersistence(config, grand_manager, shadow_manager, tracker)
            >>> path = persistence.save_regular_digest("weekly", regular_digest, "W0042_2025年11月第4週")
            >>> path.name
            'W0042_2025年11月第4週.txt'
        """
        config = self.level_config[level]
        target_dir = self.digests_path / str(config["dir"])

        log_debug(f"{LOG_PREFIX_FILE} save_regular_digest: target_dir={target_dir}")
        log_debug(f"{LOG_PREFIX_STATE} creating directory if needed")

        target_dir.mkdir(parents=True, exist_ok=True)
        final_filename = f"{new_digest_name}.txt"
        final_path = target_dir / final_filename

        log_debug(f"{LOG_PREFIX_FILE} final_path: {final_path}")
        log_debug(f"{LOG_PREFIX_FILE} file_exists: {final_path.exists()}")

        # 既存ファイルチェック
        if final_path.exists():
            log_warning(f"ファイルが既に存在します: {final_path}")
            log_debug(f"{LOG_PREFIX_DECISION} prompting for overwrite confirmation")
            if not self.confirm_callback("Overwrite?"):
                raise ValidationError("User cancelled overwrite")

        # 保存
        try:
            log_debug(f"{LOG_PREFIX_FILE} saving RegularDigest to {final_path}")
            save_json(final_path, as_dict(regular_digest))
        except IOError as e:
            formatter = get_error_formatter()
            raise FileIOError(formatter.file.file_io_error("save", final_path, e))

        _logger.info(f"RegularDigest保存完了: {final_path}")
        return final_path

    def update_grand_digest(
        self, level: str, regular_digest: RegularDigestData, new_digest_name: str
    ) -> None:
        """
        GrandDigestを更新

        Args:
            level: ダイジェストレベル
            regular_digest: RegularDigest構造体
            new_digest_name: 新しいダイジェスト名

        Raises:
            DigestError: overall_digestが無効な場合、またはGrandDigest更新に失敗した場合
        """
        _logger.info(f"[Step 2] GrandDigest.txt更新: {level}")
        overall_digest = regular_digest.get("overall_digest")
        if not overall_digest or not is_valid_dict(overall_digest):
            formatter = get_error_formatter()
            raise DigestError(
                formatter.validation.validation_error(
                    "RegularDigest", "has no valid overall_digest", None
                )
            )
        # GrandDigestManager.update_digestは例外を投げる（失敗時）
        self.grand_digest_manager.update_digest(
            level, new_digest_name, cast(OverallDigestData, overall_digest)
        )

    def _update_shadow_cascade(self, level: str) -> None:
        """
        ShadowGrandDigestのカスケード更新を実行

        Registry経由でカスケード判定（OCP準拠）。

        Args:
            level: ダイジェストレベル
        """
        registry = get_level_registry()
        should_cascade = registry.should_cascade(level)

        log_debug(f"{LOG_PREFIX_DECISION} should_cascade({level}): {should_cascade}")

        if should_cascade:
            _logger.info("[Step 3] ShadowGrandDigestカスケード処理")
            log_debug(f"{LOG_PREFIX_STATE} starting cascade for level={level}")
            self.shadow_manager.cascade_update_on_digest_finalize(level)
        else:
            _logger.info(f"[Step 3] スキップ（{level}は最上位、カスケード不要）")

    def _update_digest_times(self, level: str, source_files: List[str]) -> None:
        """
        last_digest_timesを更新

        Args:
            level: ダイジェストレベル
            source_files: ソースファイルリスト
        """
        _logger.info(f"[Step 4] last_digest_times.json更新: {level}")
        self.times_tracker.save(level, source_files)

    def _cleanup_provisional_file(self, provisional_file: Optional[Path]) -> None:
        """
        ProvisionalDigestファイルを削除

        Args:
            provisional_file: 削除するファイル（Noneの場合はスキップ）
        """
        if provisional_file and provisional_file.exists():
            try:
                provisional_file.unlink()
                _logger.info(f"[Step 5] マージ後のProvisional削除完了: {provisional_file.name}")
            except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
                # FileNotFoundError: 競合状態でファイルが既に削除された場合
                # PermissionError: ファイルがロックされている場合
                # IsADirectoryError: パスがディレクトリを指している場合
                log_warning(f"Provisionalダイジェストの削除に失敗: {e}")

    def process_cascade_and_cleanup(
        self, level: str, source_files: List[str], provisional_file_to_delete: Optional[Path]
    ) -> None:
        """
        カスケード処理とProvisional削除（オーケストレーター）

        Args:
            level: ダイジェストレベル
            source_files: ソースファイルリスト
            provisional_file_to_delete: 削除するProvisionalファイル

        Example:
            >>> persistence = DigestPersistence(config, grand_manager, shadow_manager, tracker)
            >>> persistence.process_cascade_and_cleanup("weekly", ["W0040.txt", "W0041.txt"], provisional_path)
            # ShadowGrandDigestのカスケード更新、last_digest_times更新、Provisional削除が実行される
        """
        log_debug(f"{LOG_PREFIX_STATE} process_cascade_and_cleanup: level={level}")
        log_debug(f"{LOG_PREFIX_STATE} source_files_count: {len(source_files)}")
        log_debug(f"{LOG_PREFIX_FILE} provisional_to_delete: {provisional_file_to_delete}")

        self._update_shadow_cascade(level)
        self._update_digest_times(level, source_files)
        self._cleanup_provisional_file(provisional_file_to_delete)

        log_debug(f"{LOG_PREFIX_STATE} cascade_and_cleanup completed for level={level}")
