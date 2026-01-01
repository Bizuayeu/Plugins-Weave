# adapters/process/spawner.py
"""
プロセススポーナーアダプター

デタッチドプロセスの起動を担当する。
ProcessSpawnerPort を実装。
"""
from __future__ import annotations

import subprocess
import sys


class ProcessSpawner:
    """
    デタッチドプロセスを起動するアダプター。

    WaitEssayUseCase で使用される。
    Windows と Unix で異なる起動方法を使用。
    """

    def spawn_detached(self, script_path: str) -> int:
        """
        デタッチドプロセスを起動する。

        Args:
            script_path: 実行するPythonスクリプトのパス

        Returns:
            プロセスID
        """
        if sys.platform == "win32":
            return self._spawn_windows(script_path)
        else:
            return self._spawn_unix(script_path)

    def _spawn_windows(self, script_path: str) -> int:
        """Windows用デタッチドプロセス起動"""
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008

        proc = subprocess.Popen(
            [sys.executable, script_path],
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return proc.pid

    def _spawn_unix(self, script_path: str) -> int:
        """Unix用デタッチドプロセス起動"""
        proc = subprocess.Popen(
            [sys.executable, script_path],
            start_new_session=True,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return proc.pid
