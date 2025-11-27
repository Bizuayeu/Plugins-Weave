#!/usr/bin/env python3
"""
Directory Validator
===================

ディレクトリ構造検証
"""

from pathlib import Path
from typing import List

from domain.constants import LEVEL_NAMES

from .level_path_service import LevelPathService


class DirectoryValidator:
    """ディレクトリ構造検証クラス"""

    def __init__(
        self,
        loops_path: Path,
        digests_path: Path,
        essences_path: Path,
        level_path_service: LevelPathService,
    ):
        """
        初期化

        Args:
            loops_path: Loopsディレクトリのパス
            digests_path: Digestsディレクトリのパス
            essences_path: Essencesディレクトリのパス
            level_path_service: レベルパスサービス
        """
        self.loops_path = loops_path
        self.digests_path = digests_path
        self.essences_path = essences_path
        self.level_path_service = level_path_service

    def validate_directory_structure(self) -> List[str]:
        """
        ディレクトリ構造の検証

        期待される構造:
          - loops_path が存在
          - digests_path が存在
          - essences_path が存在
          - 各レベルディレクトリ (1_Weekly, 2_Monthly, ...) が存在
          - 各レベルディレクトリ内にProvisionalが存在

        Returns:
            エラーメッセージのリスト（問題がなければ空リスト）
        """
        errors = []

        # 基本ディレクトリのチェック
        for path, name in [
            (self.loops_path, "Loops"),
            (self.digests_path, "Digests"),
            (self.essences_path, "Essences"),
        ]:
            if not path.exists():
                errors.append(f"{name} directory missing: {path}")

        # 各レベルディレクトリとProvisionalのチェック
        for level in LEVEL_NAMES:
            level_dir = self.level_path_service.get_level_dir(level)
            prov_dir = self.level_path_service.get_provisional_dir(level)

            if not level_dir.exists():
                errors.append(f"{level} directory missing: {level_dir}")
            elif not prov_dir.exists():
                # レベルディレクトリがある場合のみProvisionalをチェック
                errors.append(f"{level} Provisional missing: {prov_dir}")

        return errors
