#!/usr/bin/env python3
"""
Digest Persistence
==================

RegularDigestの保存、GrandDigest更新、カスケード処理を担当
"""

from pathlib import Path
from typing import Callable, List, Optional

from application.grand import GrandDigestManager, ShadowGrandDigestManager
from application.tracking import DigestTimesTracker
from application.validators import is_valid_dict
from config import DigestConfig
from domain.constants import LEVEL_CONFIG
from domain.exceptions import DigestError, FileIOError, ValidationError
from domain.level_registry import get_level_registry
from domain.types import RegularDigestData
from infrastructure import get_default_confirm_callback, log_info, log_warning, save_json


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
        """
        config = self.level_config[level]
        target_dir = self.digests_path / config["dir"]
        target_dir.mkdir(parents=True, exist_ok=True)
        final_filename = f"{new_digest_name}.txt"
        final_path = target_dir / final_filename

        # 既存ファイルチェック
        if final_path.exists():
            log_warning(f"File already exists: {final_path}")
            if not self.confirm_callback("Overwrite?"):
                raise ValidationError("User cancelled overwrite")

        # 保存
        try:
            save_json(final_path, regular_digest)
        except IOError as e:
            raise FileIOError(f"Failed to save RegularDigest: {e}")

        log_info(f"RegularDigest saved: {final_path}")
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
        log_info(f"[Step 2] Updating GrandDigest.txt for {level}")
        overall_digest = regular_digest.get("overall_digest")
        if not overall_digest or not is_valid_dict(overall_digest):
            raise DigestError("RegularDigest has no valid overall_digest")
        # GrandDigestManager.update_digestは例外を投げる（失敗時）
        self.grand_digest_manager.update_digest(level, new_digest_name, overall_digest)

    def _update_shadow_cascade(self, level: str) -> None:
        """
        ShadowGrandDigestのカスケード更新を実行

        Registry経由でカスケード判定（OCP準拠）。

        Args:
            level: ダイジェストレベル
        """
        registry = get_level_registry()
        if registry.should_cascade(level):
            log_info("[Step 3] Processing ShadowGrandDigest cascade")
            self.shadow_manager.cascade_update_on_digest_finalize(level)
        else:
            log_info(f"[Step 3] Skipped ({level} is top level, no cascade needed)")

    def _update_digest_times(self, level: str, source_files: List[str]) -> None:
        """
        last_digest_timesを更新

        Args:
            level: ダイジェストレベル
            source_files: ソースファイルリスト
        """
        log_info(f"[Step 4] Updating last_digest_times.json for {level}")
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
                log_info(
                    f"[Step 5] Removed Provisional digest after merge: {provisional_file.name}"
                )
            except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
                # FileNotFoundError: 競合状態でファイルが既に削除された場合
                # PermissionError: ファイルがロックされている場合
                # IsADirectoryError: パスがディレクトリを指している場合
                log_warning(f"Failed to remove Provisional digest: {e}")

    def process_cascade_and_cleanup(
        self, level: str, source_files: List[str], provisional_file_to_delete: Optional[Path]
    ) -> None:
        """
        カスケード処理とProvisional削除（オーケストレーター）

        Args:
            level: ダイジェストレベル
            source_files: ソースファイルリスト
            provisional_file_to_delete: 削除するProvisionalファイル
        """
        self._update_shadow_cascade(level)
        self._update_digest_times(level, source_files)
        self._cleanup_provisional_file(provisional_file_to_delete)
