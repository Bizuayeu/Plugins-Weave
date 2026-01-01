# adapters/storage/path_resolver.py
"""
パス解決アダプター

永続化ディレクトリやランナースクリプト用ディレクトリのパス解決を担当。
PathResolverPort を実装。

Stage 5.1: ストレージアダプター責務分離
"""

from __future__ import annotations

from pathlib import Path

PERSISTENT_DIR_NAME = ".emailingessay"


class PathResolverAdapter:
    """
    パス解決アダプター（PathResolverPort実装）

    永続化ディレクトリとランナースクリプト用ディレクトリのパスを解決する。
    """

    def __init__(self, base_dir: str | None = None) -> None:
        """
        Args:
            base_dir: 基底ディレクトリ（テスト用）。Noneの場合はデフォルトを使用
        """
        self._base_dir = Path(base_dir) if base_dir else None

    def get_persistent_dir(self) -> str:
        """
        永続化ディレクトリのパスを取得（なければ作成）。

        Returns:
            永続化ディレクトリのパス
        """
        if self._base_dir:
            self._base_dir.mkdir(parents=True, exist_ok=True)
            return str(self._base_dir)

        persistent_dir = Path.home() / ".claude" / "plugins" / PERSISTENT_DIR_NAME
        persistent_dir.mkdir(parents=True, exist_ok=True)
        return str(persistent_dir)

    def get_runners_dir(self) -> str:
        """
        ランナースクリプト用ディレクトリのパスを取得（なければ作成）。

        Returns:
            ランナースクリプト用ディレクトリのパス
        """
        runners_dir = Path(self.get_persistent_dir()) / "runners"
        runners_dir.mkdir(parents=True, exist_ok=True)
        return str(runners_dir)
