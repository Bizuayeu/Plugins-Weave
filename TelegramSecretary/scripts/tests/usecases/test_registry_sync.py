"""R2-1: RegistrySyncService（管理表の git 永続化ロジック）のテスト。

commit/push 分離 + non-ff 時の pull_rebase フォールバックを fake GitSync で全分岐検証。
"""
from __future__ import annotations

from pathlib import Path

from domain.exceptions import GitSyncError, PushRejectedError
from usecases.registry_sync import RegistrySyncService

from tests.usecases.fakes import FakeGitSync

_PATHS = [Path("registry/individuals/INDIVIDUALS.json")]
_MSG = "registry: add individual u1"


def test_sync_no_change_skips_push():
    """変更が無ければ commit は no-op、push も呼ばない。"""
    git = FakeGitSync(committed=False)
    result = RegistrySyncService(git).sync(_PATHS, _MSG)
    assert result.committed is False
    assert result.pushed is False
    assert result.rebased is False
    assert git.push_calls == 0


def test_sync_commit_then_push_success():
    """commit あり → push 成功（rebase 不要）。"""
    git = FakeGitSync(committed=True, push_outcomes=[None])
    result = RegistrySyncService(git).sync(_PATHS, _MSG)
    assert result.committed is True
    assert result.pushed is True
    assert result.rebased is False
    assert git.push_calls == 1
    assert git.pull_rebase_calls == 0
    assert git.commit_calls[0] == (_PATHS, _MSG)


def test_sync_non_ff_triggers_rebase_then_push():
    """push が non-ff（PushRejectedError）→ pull_rebase → 再 push 成功。"""
    git = FakeGitSync(committed=True, push_outcomes=[PushRejectedError("non-ff"), None])
    result = RegistrySyncService(git).sync(_PATHS, _MSG)
    assert result.committed is True
    assert result.pushed is True
    assert result.rebased is True
    assert git.pull_rebase_calls == 1
    assert git.push_calls == 2


def test_sync_push_network_failure_keeps_commit():
    """push がネットワーク失敗（GitSyncError）→ commit は残す（best-effort、rebase しない）。"""
    git = FakeGitSync(committed=True, push_outcomes=[GitSyncError("network")])
    result = RegistrySyncService(git).sync(_PATHS, _MSG)
    assert result.committed is True
    assert result.pushed is False
    assert result.rebased is False
    assert git.pull_rebase_calls == 0


def test_sync_rebase_then_push_still_fails_keeps_commit():
    """non-ff → rebase → 再 push も失敗 → commit は残す（rebased=True, pushed=False）。"""
    git = FakeGitSync(
        committed=True, push_outcomes=[PushRejectedError("non-ff"), GitSyncError("still")]
    )
    result = RegistrySyncService(git).sync(_PATHS, _MSG)
    assert result.committed is True
    assert result.pushed is False
    assert result.rebased is True
    assert git.push_calls == 2
    assert git.pull_rebase_calls == 1
