"""GitSyncPort の subprocess 実装（R2-2）。

registry_dir を含む git リポで、管理表の commit/push/pull-rebase/fetch を実行する。
git メッセージは LC_ALL=C で英語固定し non-fast-forward を確実に検出する。
固定ブランチ運用・force 不使用の競合設計は DESIGN.md §3.6 を参照。
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import List, Sequence

from domain.exceptions import GitSyncError, PushRejectedError, RegistryWorktreeError

# git push 拒否（non-fast-forward）の英語マーカー（LC_ALL=C 固定で安定検出）。
# "rejected" は部分文字列マッチで "[rejected]" を包含するため後者は列挙しない。
_NON_FF_MARKERS = ("non-fast-forward", "fetch first", "rejected")


class GitCliAdapter:
    """GitSyncPort を git CLI（subprocess）で実装する。

    repo_dir 配下を作業ツリーとし、固定 branch を remote へ push する。
    認証（PAT 等）は環境（git credential / URL 埋め込み）に委ね、本 Adapter は持たない。
    """

    def __init__(
        self, repo_dir, remote: str = "origin", branch: str = "claude/ts-registry"
    ) -> None:
        self._repo = Path(repo_dir)
        self._remote = remote
        self._branch = branch

    def _run(self, args: Sequence[str], check: bool = True) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(
                ["git", *args],
                cwd=str(self._repo),
                capture_output=True,
                text=True,
                env={**os.environ, "LC_ALL": "C", "LANG": "C"},
            )
        except OSError as exc:
            # registry_root が未作成の初回起動（cwd 不在）や git バイナリ不在で
            # subprocess を起動できないケースを domain の GitSyncError に翻訳する。
            # これにより run_registry_fetch が「fetch 失敗＝transient」として握り、
            # 空のローカル管理表で継続できる（SETUP.md「初回は対象ブランチが空でも継続」）。
            raise GitSyncError(f"git {' '.join(args)} could not run: {exc}") from None
        if check and result.returncode != 0:
            raise GitSyncError(
                f"git {' '.join(args)} failed (rc={result.returncode}): {result.stderr.strip()}"
            )
        return result

    def commit(self, paths: List[Path], message: str) -> bool:
        """paths を stage して commit。staged 差分が無ければ False（no-op）。"""
        self._run(["add", "--", *[str(p) for p in paths]])
        staged = self._run(["diff", "--cached", "--quiet"], check=False)
        if staged.returncode == 0:
            return False  # staged 差分なし＝変更なし
        self._run(["commit", "-m", message])
        return True

    def push(self) -> None:
        """HEAD を remote の固定 branch へ push。non-ff は PushRejectedError、他は GitSyncError。"""
        result = self._run(["push", self._remote, f"HEAD:{self._branch}"], check=False)
        if result.returncode != 0:
            blob = (result.stderr + "\n" + result.stdout).lower()
            if any(m in blob for m in _NON_FF_MARKERS):
                raise PushRejectedError(result.stderr.strip())
            raise GitSyncError(f"git push failed: {result.stderr.strip()}")

    def pull_rebase(self) -> None:
        """remote の固定 branch を pull --rebase で取り込む（外部更新の統合）。"""
        self._run(["pull", "--rebase", self._remote, self._branch])

    def _assert_independent_worktree(self) -> None:
        """cwd が registry_dir を root とする独立 git 作業ツリーか検証する（層2 防御ガード）。

        registry_dir が他リポ（親 Private 等）の作業ツリー内サブディレクトリだと、
        checkout -B が親リポ全体のブランチを切り替えて破壊する（潜在第二欠陥）。
        show-toplevel が registry_dir 自身と一致しなければ checkout を撃たず停止する。
        registry_dir 不在/git 管理外なら _run が OSError/非0 を GitSyncError に翻訳する
        （初回起動の transient 経路、SETUP.md「初回は対象ブランチが空でも継続」）。
        """
        result = self._run(["rev-parse", "--show-toplevel"])
        toplevel = Path(result.stdout.strip()).resolve()
        expected = self._repo.resolve()
        if toplevel != expected:
            raise RegistryWorktreeError(
                f"registry_dir is not an independent git work tree: "
                f"expected top-level {expected}, got {toplevel}. "
                f"checkout -B aborted to avoid corrupting the parent repository."
            )

    def fetch_checkout(self, branch: str) -> None:
        """remote の branch を fetch し、ローカルを origin/branch に合わせて checkout（起動時の最新取得）。

        checkout -B は cwd の作業ツリー全体を branch へ切り替えるため、cwd が registry_dir を
        root とする独立作業ツリーであることを先に検証する（親リポ誤爆の構造的禁止、層2）。
        """
        self._assert_independent_worktree()
        self._run(["fetch", self._remote, branch])
        self._run(["checkout", "-B", branch, f"{self._remote}/{branch}"])
