from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from domain.authorization import AuthorizedChats
from infrastructure.config import Config
from infrastructure.registry_cli import run_registry_command, run_registry_fetch
from usecases.registry_sync import RegistrySyncService

from tests.usecases.fakes import FakeGitSync


def _config(tmp_path: Path) -> Config:
    return Config(
        bot_token="x",
        authorized_chats=AuthorizedChats.from_iterable([1]),
        state_dir=tmp_path,
        session_duration_sec=7200,
    )


def _ns(**kw) -> argparse.Namespace:
    base = {"key": None, "json": None, "json_file": None}
    base.update(kw)
    return argparse.Namespace(**base)


_INDIVIDUAL = {
    "uuid": "u1", "display_name": "yamada", "role": "associate",
    "status": "active", "created_at": "t", "updated_at": "t",
}


def test_add_then_get_individual(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))) == 0
    assert run_registry_command(config, "individuals", "get", _ns(key="u1")) == 0
    assert "yamada" in capsys.readouterr().out


def test_add_invalid_role_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_INDIVIDUAL, role="boss")
    assert run_registry_command(config, "individuals", "add", _ns(json=json.dumps(bad))) == 2


def test_list_empty_prints_empty_array(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "individuals", "list", _ns()) == 0
    assert capsys.readouterr().out.strip() == "[]"


def test_get_missing_returns_2(tmp_path):
    config = _config(tmp_path)
    assert run_registry_command(config, "tasks", "get", _ns(key="zzz")) == 2


def test_remove_individual(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL)))
    assert run_registry_command(config, "individuals", "remove", _ns(key="u1")) == 0
    assert run_registry_command(config, "individuals", "get", _ns(key="u1")) == 2


def test_add_persists_to_correct_path(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL)))
    assert config.individuals_path.exists()


def test_add_persists_to_registry_dir_when_set(tmp_path):
    """registry_dir 指定時、管理表は state_dir でなく registry_dir 配下に書かれる（揮発/永続分離）。"""
    state = tmp_path / "volatile"
    reg = tmp_path / "registry"
    config = Config(
        bot_token="x",
        authorized_chats=AuthorizedChats.from_iterable([1]),
        state_dir=state,
        session_duration_sec=7200,
        registry_dir=reg,
    )
    run_registry_command(config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL)))
    assert (reg / "individuals" / "INDIVIDUALS.json").exists()
    assert not (state / "individuals").exists()


# === R2-3: イベント駆動 sync（DI） ===


def test_add_triggers_sync_when_provided(tmp_path):
    """sync 注入時、add 成功後に sync が走る（commit→push）。"""
    config = _config(tmp_path)
    git = FakeGitSync()
    run_registry_command(
        config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL)),
        sync=RegistrySyncService(git),
    )
    assert len(git.commit_calls) == 1
    assert git.push_calls == 1


def test_remove_triggers_sync_when_provided(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL)))
    git = FakeGitSync()
    run_registry_command(
        config, "individuals", "remove", _ns(key="u1"),
        sync=RegistrySyncService(git),
    )
    assert len(git.commit_calls) == 1


def test_list_does_not_trigger_sync(tmp_path):
    """list は読み取りゆえ sync しない。"""
    config = _config(tmp_path)
    git = FakeGitSync()
    run_registry_command(config, "individuals", "list", _ns(), sync=RegistrySyncService(git))
    assert git.commit_calls == []


def test_no_sync_when_not_provided(tmp_path):
    """sync 未注入なら従来通り（後方互換、git に触れない）。"""
    config = _config(tmp_path)
    assert run_registry_command(
        config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))
    ) == 0


# === R2-3c: 起動時 fetch（registry-sync） ===


def test_registry_fetch_calls_fetch_checkout_when_enabled(tmp_path):
    """registry_sync 有効時、固定ブランチを fetch_checkout で引く（起動時の最新取得）。"""
    config = Config(
        bot_token="x",
        authorized_chats=AuthorizedChats.from_iterable([1]),
        state_dir=tmp_path,
        session_duration_sec=7200,
        registry_sync_enabled=True,
        registry_branch="claude/ts-registry",
    )
    git = FakeGitSync()
    assert run_registry_fetch(config, git=git) == 0
    assert git.fetch_calls == ["claude/ts-registry"]


def test_registry_fetch_noop_when_disabled(tmp_path):
    """registry_sync 無効なら fetch しない（no-op、後方互換）。"""
    config = _config(tmp_path)
    git = FakeGitSync()
    assert run_registry_fetch(config, git=git) == 0
    assert git.fetch_calls == []


def test_registry_fetch_continues_when_registry_root_absent(tmp_path):
    """初回起動で registry_root が物理的に未作成でも、クラッシュせず fetch 失敗
    （EXIT_FETCH_FAILED=1）として握り、空のローカル管理表で継続できる。

    実 GitCliAdapter を不在ディレクトリに向け、subprocess の OSError が
    domain の GitSyncError に翻訳されること（OSError を漏らさないこと）を保証する
    ──SETUP.md「初回は対象ブランチが空でも継続」の実装回帰テスト。
    """
    from adapters.registry.git_cli import GitCliAdapter
    from domain.exceptions import GitSyncError

    missing = tmp_path / "never-created" / "registry"
    config = Config(
        bot_token="x",
        authorized_chats=AuthorizedChats.from_iterable([1]),
        state_dir=tmp_path,
        session_duration_sec=7200,
        registry_sync_enabled=True,
        registry_dir=missing,
        registry_branch="claude/ts-registry",
    )
    adapter = GitCliAdapter(config.registry_root, branch=config.registry_branch)

    # OSError ではなく domain の GitSyncError に翻訳される（cwd 不在で git を起動できない）
    with pytest.raises(GitSyncError):
        adapter.fetch_checkout(config.registry_branch)

    # ハンドラは transient 扱いで EXIT_FETCH_FAILED（=1）を返し、例外を投げない
    assert run_registry_fetch(config, git=adapter) == 1
