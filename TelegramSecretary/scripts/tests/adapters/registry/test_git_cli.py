"""R2-2: GitCliAdapter（GitSyncPort の subprocess 実装）の integration テスト。

実 git で bare remote + work clone を立て、commit/push/non-ff/rebase/fetch を round-trip 検証。
git 不在環境では skip。git メッセージは LC_ALL=C で英語固定（non-ff 検出の安定化）。
"""
from __future__ import annotations

import os
import shutil
import subprocess

import pytest

import adapters.registry.git_cli as git_cli
from adapters.registry.git_cli import GitCliAdapter
from domain.exceptions import GitSyncError, PushRejectedError, RegistryWorktreeError

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


# --- subprocess モックによるハング・credential 安全弁の単体検証 ---
# （実 git 不要だが、ファイル先頭の skipif を共有する——integration と同居の流儀）


def test_run_sets_timeout_and_disables_credential_prompt(tmp_path, monkeypatch):
    """全 git subprocess に timeout と GIT_TERMINAL_PROMPT=0 が入る。

    credential 未設定の push/fetch が認証プロンプト待ちで永久ブロックすると、
    WAL push は送信ゲートゆえ秘書のターン全体が無期限停止する——二重の安全弁で遮断。
    """
    recorded = {}

    def fake_run(cmd, **kwargs):
        recorded["cmd"] = cmd
        recorded["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(git_cli.subprocess, "run", fake_run)
    GitCliAdapter(tmp_path).push()
    assert recorded["kwargs"]["timeout"] == 90
    assert recorded["kwargs"]["env"]["GIT_TERMINAL_PROMPT"] == "0"


def test_timeout_expired_translates_to_git_sync_error(tmp_path, monkeypatch):
    """TimeoutExpired は domain の GitSyncError に翻訳される（subprocess 例外を漏らさない）。"""

    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=90)

    monkeypatch.setattr(git_cli.subprocess, "run", fake_run)
    with pytest.raises(GitSyncError) as ei:
        GitCliAdapter(tmp_path).push()
    assert "timed out" in str(ei.value)


def test_pull_rebase_failure_aborts_inprogress_rebase_then_raises(tmp_path, monkeypatch):
    """pull --rebase 失敗時は rebase --abort を best-effort で撃ってから raise する。

    rebase-in-progress を放置すると以降の commit/push が全滅し自己復旧不能になる
    （「失敗してもクリーンな作業ツリー」不変条件）。
    """
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[1] == "pull":
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="CONFLICT (content)")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(git_cli.subprocess, "run", fake_run)
    with pytest.raises(GitSyncError):
        GitCliAdapter(tmp_path).pull_rebase()
    assert ["git", "rebase", "--abort"] in calls


def test_pull_rebase_success_does_not_abort(tmp_path, monkeypatch):
    """成功経路では rebase --abort を撃たない（成功直後の作業ツリーを巻き戻さない）。"""
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(git_cli.subprocess, "run", fake_run)
    GitCliAdapter(tmp_path).pull_rebase()
    assert ["git", "rebase", "--abort"] not in calls


_CRED_STDERR = (
    "fatal: unable to access "
    "'https://x-access-token:ghp_SECRETSECRET@github.com/o/r.git/': 403"
)


def test_run_failure_scrubs_credentials_from_message(tmp_path, monkeypatch):
    """URL 埋め込み PAT が例外メッセージへ素通りしない（telegram 側の redact 規律と対称化）。"""

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 128, stdout="", stderr=_CRED_STDERR)

    monkeypatch.setattr(git_cli.subprocess, "run", fake_run)
    with pytest.raises(GitSyncError) as ei:
        GitCliAdapter(tmp_path).pull_rebase()
    assert "ghp_SECRETSECRET" not in str(ei.value)
    assert "://***@" in str(ei.value)


def test_push_rejected_scrubs_credentials_from_message(tmp_path, monkeypatch):
    """push の check=False 経路（PushRejectedError / GitSyncError 両方）もスクラブを通す。"""

    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd, 1, stdout="", stderr=_CRED_STDERR + "\n ! [rejected] (fetch first)"
        )

    monkeypatch.setattr(git_cli.subprocess, "run", fake_run)
    with pytest.raises(PushRejectedError) as ei:
        GitCliAdapter(tmp_path).push()
    assert "ghp_SECRETSECRET" not in str(ei.value)
    assert "://***@" in str(ei.value)


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
