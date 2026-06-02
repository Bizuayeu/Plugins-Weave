"""管理表の git 永続化ロジック（R2-1）。

イベント駆動 commit & push。commit はローカル即時（確実）、push は best-effort
（non-fast-forward は pull --rebase で取り込んで再 push、ネットワーク失敗はローカル commit を残す）。
git 操作は GitSyncPort（adapters 実装）越し。固定ブランチ運用・force 不使用の競合設計は
docs/devlog/REGISTRY_PERSISTENCE_PLAN.md を参照。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from domain.exceptions import GitSyncError, PushRejectedError
from usecases.ports import GitSyncPort


@dataclass(frozen=True)
class SyncResult:
    """sync の結果。

    - committed: ローカル commit したか（変更が無ければ False）
    - pushed: リモートへ反映できたか
    - rebased: 外部更新を pull --rebase で取り込んだか
    """

    committed: bool
    pushed: bool
    rebased: bool


class RegistrySyncService:
    """管理表更新後の git 同期（commit → push、non-ff は rebase フォールバック）。"""

    def __init__(self, git: GitSyncPort) -> None:
        self._git = git

    def sync(self, paths: List[Path], message: str) -> SyncResult:
        """paths を commit（ローカル即時）し push（best-effort）する。

        - 変更が無ければ commit は no-op で push もしない
        - push 成功 → done
        - push が non-ff（PushRejectedError）→ pull_rebase → 再 push
        - push がネットワーク等で失敗（GitSyncError）→ commit は残す（次回 sync で再 push）
        """
        committed = self._git.commit(paths, message)
        if not committed:
            return SyncResult(committed=False, pushed=False, rebased=False)
        return self._try_push()

    def _try_push(self) -> SyncResult:
        """commit 済み前提で push を試みる。non-ff は rebase して 1 度だけ再 push。"""
        try:
            self._git.push()
            return SyncResult(committed=True, pushed=True, rebased=False)
        except PushRejectedError:
            # 外部更新あり: 取り込んで再 push（独立ファイルは git が自動マージ）
            self._git.pull_rebase()
            try:
                self._git.push()
                return SyncResult(committed=True, pushed=True, rebased=True)
            except GitSyncError:
                return SyncResult(committed=True, pushed=False, rebased=True)
        except GitSyncError:
            # ネットワーク等: best-effort、commit は残る（次回 sync でまとめて push）
            return SyncResult(committed=True, pushed=False, rebased=False)
