#!/usr/bin/env python3
"""
Digest Persistence
==================

RegularDigestの保存、GrandDigest更新、カスケード処理を担当
"""

from pathlib import Path
from typing import Dict, Any, Optional, List

from config import DigestConfig, LEVEL_CONFIG
from validators import is_valid_dict
from exceptions import DigestError, FileIOError, ValidationError
from utils import log_info, log_warning, save_json
from grand_digest import GrandDigestManager
from shadow_grand_digest import ShadowGrandDigestManager
from digest_times import DigestTimesTracker


class DigestPersistence:
    """ダイジェストの永続化処理を担当"""

    def __init__(
        self,
        config: DigestConfig,
        grand_digest_manager: GrandDigestManager,
        shadow_manager: ShadowGrandDigestManager,
        times_tracker: DigestTimesTracker
    ):
        """
        Args:
            config: DigestConfig インスタンス
            grand_digest_manager: GrandDigestManager インスタンス
            shadow_manager: ShadowGrandDigestManager インスタンス
            times_tracker: DigestTimesTracker インスタンス
        """
        self.config = config
        self.digests_path = config.digests_path
        self.grand_digest_manager = grand_digest_manager
        self.shadow_manager = shadow_manager
        self.times_tracker = times_tracker
        self.level_config = LEVEL_CONFIG

    def save_regular_digest(
        self, level: str, regular_digest: Dict[str, Any], new_digest_name: str
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
            try:
                response = input("Overwrite? (y/n): ")
                if response.lower() != 'y':
                    raise ValidationError("User cancelled overwrite")
            except EOFError:
                log_info("Non-interactive mode: overwriting existing file")

        # 保存
        try:
            save_json(final_path, regular_digest)
        except IOError as e:
            raise FileIOError(f"Failed to save RegularDigest: {e}")

        log_info(f"RegularDigest saved: {final_path}")
        return final_path

    def update_grand_digest(
        self, level: str, regular_digest: Dict[str, Any], new_digest_name: str
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
        print(f"\n[処理2] Updating GrandDigest.txt for {level}")
        overall_digest = regular_digest.get("overall_digest")
        if not overall_digest or not is_valid_dict(overall_digest):
            raise DigestError("RegularDigest has no valid overall_digest")
        # GrandDigestManager.update_digestは例外を投げる（失敗時）
        self.grand_digest_manager.update_digest(level, new_digest_name, overall_digest)

    def process_cascade_and_cleanup(
        self, level: str, source_files: List[str], provisional_file_to_delete: Optional[Path]
    ) -> None:
        """
        カスケード処理とProvisional削除

        Args:
            level: ダイジェストレベル
            source_files: ソースファイルリスト
            provisional_file_to_delete: 削除するProvisionalファイル
        """
        # ShadowGrandDigest更新（カスケード）
        if level != "centurial":
            print(f"\n[処理3] Processing ShadowGrandDigest cascade")
            self.shadow_manager.cascade_update_on_digest_finalize(level)
        else:
            print(f"\n[処理3] Skipped (Centurial is top level, no cascade needed)")

        # last_digest_times更新
        print(f"\n[処理4] Updating last_digest_times.json for {level}")
        self.times_tracker.save(level, source_files)

        # ProvisionalDigest削除（クリーンアップ）
        if provisional_file_to_delete and provisional_file_to_delete.exists():
            try:
                provisional_file_to_delete.unlink()
                print(f"\n[処理5] Removed Provisional digest after merge: {provisional_file_to_delete.name}")
            except OSError as e:
                log_warning(f"Failed to remove Provisional digest: {e}")
