"""R2-2: GitCliAdapter（GitSyncPort の subprocess 実装）の integration テスト。

実 git で bare remote + work clone を立て、commit/push/non-ff/rebase/fetch を round-trip 検証。
git 不在環境では skip。git メッセージは LC_ALL=C で英語固定（non-ff 検出の安定化）。
"""
from __future__ import annotations

import os
import shutil
import subprocess

import pytest

from adapters.registry.git_cli import GitCliAdapter
from domain.exceptions import PushRejectedError, RegistryWorktreeError

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")

_BRANCH = "claude/ts-registry"
_ENV = {**os.environ, "LC_ALL": "C", "LANG": "C"}


def _git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, check=True, env=_ENV,
    )


@pytest.fixture
def repos(tmp_path):
    """bare remote + work clone（registry ブランチに initial commit を push 済み）。"""
    remote = tmp_path / "remote.git"
    subprocess.run(["git", "init", "--bare", "-b", "main", str(remote)],
                   check=True, capture_output=True, env=_ENV)
    work = tmp_path / "work"
    subprocess.run(["git", "init", "-b", "main", str(work)],
                   check=True, capture_output=True, env=_ENV)
    _git(work, "config", "user.email", "t@example.com")
    _git(work, "config", "user.name", "Tester")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "checkout", "-b", _BRANCH)
    (work / ".keep").write_text("", encoding="utf-8")
    _git(work, "add", ".keep")
    _git(work, "commit", "-m", "init")
    _git(work, "push", "origin", _BRANCH)
    return work, remote


def _clone_and_advance(remote, tmp_path, name):
    """別 clone が registry ブランチに 1 commit 足して push（外部更新の模擬）。"""
    other = tmp_path / name
    subprocess.run(["git", "clone", "-b", _BRANCH, str(remote), str(other)],
                   check=True, capture_output=True, env=_ENV)
    _git(other, "config", "user.email", "o@example.com")
    _git(other, "config", "user.name", "Other")
    (other / f"{name}.json").write_text("{}", encoding="utf-8")
    _git(other, "add", f"{name}.json")
    _git(other, "commit", "-m", f"{name} update")
    _git(other, "push", "origin", _BRANCH)


def test_commit_stages_and_commits(repos):
    work, _ = repos
    adapter = GitCliAdapter(work, branch=_BRANCH)
    f = work / "individuals.json"
    f.write_text('{"records":[]}', encoding="utf-8")
    assert adapter.commit([f], "registry: add individuals") is True
    assert "add individuals" in _git(work, "log", "--oneline").stdout


def test_commit_no_change_returns_false(repos):
    work, _ = repos
    adapter = GitCliAdapter(work, branch=_BRANCH)
    f = work / "x.json"
    f.write_text("a", encoding="utf-8")
    adapter.commit([f], "first")
    assert adapter.commit([f], "second-noop") is False


def test_push_reflects_to_remote(repos, tmp_path):
    work, remote = repos
    adapter = GitCliAdapter(work, branch=_BRANCH)
    f = work / "k.json"
    f.write_text("v", encoding="utf-8")
    adapter.commit([f], "add k")
    adapter.push()
    verify = tmp_path / "verify"
    subprocess.run(["git", "clone", "-b", _BRANCH, str(remote), str(verify)],
                   check=True, capture_output=True, env=_ENV)
    assert (verify / "k.json").exists()


def test_push_non_ff_raises_push_rejected(repos, tmp_path):
    work, remote = repos
    adapter = GitCliAdapter(work, branch=_BRANCH)
    _clone_and_advance(remote, tmp_path, "other")  # remote が先に進む
    f = work / "z.json"
    f.write_text("z", encoding="utf-8")
    adapter.commit([f], "work update")  # 古い HEAD から commit
    with pytest.raises(PushRejectedError):
        adapter.push()


def test_pull_rebase_resolves_non_ff(repos, tmp_path):
    work, remote = repos
    adapter = GitCliAdapter(work, branch=_BRANCH)
    _clone_and_advance(remote, tmp_path, "other")
    f = work / "z.json"
    f.write_text("z", encoding="utf-8")
    adapter.commit([f], "work update")
    with pytest.raises(PushRejectedError):
        adapter.push()
    adapter.pull_rebase()   # 外部更新を取り込む（独立ファイルは自動マージ）
    adapter.push()          # 今度は成功
    verify = tmp_path / "verify"
    subprocess.run(["git", "clone", "-b", _BRANCH, str(remote), str(verify)],
                   check=True, capture_output=True, env=_ENV)
    assert (verify / "z.json").exists()      # work の更新
    assert (verify / "other.json").exists()  # 外部更新も保持


def test_fetch_checkout_gets_remote_state(repos, tmp_path):
    work, remote = repos
    adapter = GitCliAdapter(work, branch=_BRANCH)
    _clone_and_advance(remote, tmp_path, "other")  # remote に other.json
    adapter.fetch_checkout(_BRANCH)
    assert (work / "other.json").exists()  # origin の最新が work に反映


def test_fetch_checkout_rejects_when_toplevel_differs(repos):
    """registry_dir が独立作業ツリーでなく親リポ subdir のとき、checkout -B を撃たず
    RegistryWorktreeError で停止する（親リポ誤爆＝潜在第二欠陥の遮断、層2）。
    toplevel 一致時の proceeds は test_fetch_checkout_gets_remote_state が担保。"""
    work, _ = repos
    _git(work, "checkout", "-b", "dev-work")  # 親リポは別ブランチで作業中
    subdir = work / "registry"                # work（独立ツリー）の内側の subdir
    subdir.mkdir()
    adapter = GitCliAdapter(subdir, branch=_BRANCH)
    with pytest.raises(RegistryWorktreeError):
        adapter.fetch_checkout(_BRANCH)
    # checkout -B が撃たれていない＝親リポ（work）のブランチが切り替わっていない
    assert _git(work, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip() == "dev-work"
