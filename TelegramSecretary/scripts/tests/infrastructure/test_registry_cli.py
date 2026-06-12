from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from domain.authorization import AuthorizedChats
from domain.exceptions import GitSyncError
from infrastructure.config import Config
from infrastructure.registry_cli import run_registry_command, run_registry_fetch
from usecases.registry_sync import RegistrySyncService

from tests.usecases.fakes import FakeGitSync


def _config(
    tmp_path: Path,
    sync: bool = False,
    registry_dir: Path | None = None,
) -> Config:
    """テスト用 Config（test_wal_cli.py の _config と同型の組み立てヘルパ）。"""
    return Config(
        bot_token="x",
        authorized_chats=AuthorizedChats.from_iterable([1]),
        state_dir=tmp_path,
        session_duration_sec=7200,
        registry_sync_enabled=sync,
        registry_dir=registry_dir,
        registry_branch="claude/ts-registry",
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


# === add の入力不正はクラッシュではなく EXIT_CONFIG_INVALID（例外捕捉の対称性）===


def test_add_without_json_or_json_file_returns_2(tmp_path, capsys):
    """--json / --json-file 両方未指定は入力不正（exit 2）。

    旧実装は json.loads(None) の TypeError が未捕捉で exit 1（transient の誤シグナル）
    だった。明示メッセージの ValueError 化＋捕捉統一で設定不正として返す。
    """
    config = _config(tmp_path)
    assert run_registry_command(config, "individuals", "add", _ns()) == 2
    assert "--json" in capsys.readouterr().err  # どう直せばよいかが stderr で分かる


def test_add_with_missing_json_file_returns_2(tmp_path, capsys):
    """--json-file の不在パスは入力不正（exit 2）。FileNotFoundError でクラッシュさせない。"""
    config = _config(tmp_path)
    ns = _ns(json_file=str(tmp_path / "nope.json"))
    assert run_registry_command(config, "individuals", "add", ns) == 2
    assert "invalid individuals record" in capsys.readouterr().err


def test_add_persists_to_registry_dir_when_set(tmp_path):
    """registry_dir 指定時、管理表は state_dir でなく registry_dir 配下に書かれる（揮発/永続分離）。"""
    state = tmp_path / "volatile"
    reg = tmp_path / "registry"
    config = _config(state, registry_dir=reg)
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
    config = _config(tmp_path, sync=True)
    git = FakeGitSync()
    assert run_registry_fetch(config, git=git) == 0
    assert git.fetch_calls == ["claude/ts-registry"]


def test_registry_fetch_noop_when_disabled(tmp_path):
    """registry_sync 無効なら fetch しない（no-op、後方互換）。"""
    config = _config(tmp_path)
    git = FakeGitSync()
    assert run_registry_fetch(config, git=git) == 0
    assert git.fetch_calls == []


def test_registry_fetch_continues_when_registry_root_absent(tmp_path, capsys):
    """初回起動で registry_root が物理的に未作成でも、クラッシュせず fetch 失敗
    （EXIT_FETCH_FAILED=1）として握り、空のローカル管理表で継続できる。

    実 GitCliAdapter を不在ディレクトリに向け、subprocess の OSError が
    domain の GitSyncError に翻訳されること（OSError を漏らさないこと）を保証する
    ──SETUP.md「初回は対象ブランチが空でも継続」の実装回帰テスト。
    """
    from adapters.registry.git_cli import GitCliAdapter

    missing = tmp_path / "never-created" / "registry"
    config = _config(tmp_path, sync=True, registry_dir=missing)
    adapter = GitCliAdapter(config.registry_root, branch=config.registry_branch)

    # OSError ではなく domain の GitSyncError に翻訳される（cwd 不在で git を起動できない）
    with pytest.raises(GitSyncError):
        adapter.fetch_checkout(config.registry_branch)

    # ハンドラは transient 扱いで EXIT_FETCH_FAILED（=1）を返し、例外を投げない。
    # かつ「空表で継続＝記憶なし稼働」を沈黙せず警告で明示する（層3 可観測性）。
    assert run_registry_fetch(config, git=adapter) == 1
    assert "empty" in capsys.readouterr().err.lower()


def test_registry_fetch_emits_empty_load_warning_on_failure(tmp_path, capsys):
    """fetch 失敗時、空表で継続する旨（記憶なし稼働）を警告レベルで明示する（層3）。
    transient を沈黙して握り潰す → 気づけない空表稼働、を防ぐ。"""
    config = _config(tmp_path, sync=True)
    git = FakeGitSync(fetch_outcomes=[GitSyncError("simulated fetch failure")])
    assert run_registry_fetch(config, git=git) == 1
    err = capsys.readouterr().err.lower()
    assert "warning" in err and "empty" in err  # 警告レベルで空表継続を明示


def test_registry_fetch_silent_on_success_and_noop(tmp_path, capsys):
    """成功時・no-op（registry_sync 無効）時は空表警告を出さない（偽陽性の沈黙破り防止）。"""
    enabled = _config(tmp_path, sync=True)
    assert run_registry_fetch(enabled, git=FakeGitSync()) == 0  # fetch 成功
    assert "empty" not in capsys.readouterr().err.lower()

    assert run_registry_fetch(_config(tmp_path), git=FakeGitSync()) == 0  # no-op（無効）
    assert "empty" not in capsys.readouterr().err.lower()


# === abilities（4 表目、registry 同格・WAL 対象）===


_ABILITY = {
    "id": "precognitive-viewer", "name": "三位占術鑑定",
    "created_at": "t", "updated_at": "t",
}


def test_add_then_get_ability(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "abilities", "add", _ns(json=json.dumps(_ABILITY))) == 0
    assert run_registry_command(config, "abilities", "get", _ns(key="precognitive-viewer")) == 0
    assert "precognitive-viewer" in capsys.readouterr().out


def test_ability_persists_to_abilities_path(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "abilities", "add", _ns(json=json.dumps(_ABILITY)))
    assert config.abilities_path.exists()


def test_ability_rejects_empty_name_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_ABILITY, name="")
    assert run_registry_command(config, "abilities", "add", _ns(json=json.dumps(bad))) == 2


# === P/A 軸 3 表（PROFILE / GOALS / STEPS、registry 同格・WAL 対象）===


_PROFILE = {
    "id": "pf1", "subject": "principal", "method": "mbti",
    "content": "INTJ", "created_at": "t", "updated_at": "t",
}
_GOAL = {
    "id": "g1", "title": "半年で貯蓄30万円", "category": "money",
    "status": "active", "created_at": "t", "updated_at": "t",
}
_STEP = {
    "id": "s1", "goal_id": "g1", "title": "固定費一覧を作る",
    "created_at": "t", "updated_at": "t",
}


def test_add_then_get_profile(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "profile", "add", _ns(json=json.dumps(_PROFILE))) == 0
    assert run_registry_command(config, "profile", "get", _ns(key="pf1")) == 0
    assert "principal" in capsys.readouterr().out


def test_profile_persists_to_profile_path(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "profile", "add", _ns(json=json.dumps(_PROFILE)))
    assert config.profile_path.exists()


def test_profile_rejects_invalid_method_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_PROFILE, method="palm_reading")
    assert run_registry_command(config, "profile", "add", _ns(json=json.dumps(bad))) == 2


def test_add_then_get_goal(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "goals", "add", _ns(json=json.dumps(_GOAL))) == 0
    assert run_registry_command(config, "goals", "get", _ns(key="g1")) == 0
    assert "money" in capsys.readouterr().out


def test_goal_rejects_invalid_category_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_GOAL, category="gambling")
    assert run_registry_command(config, "goals", "add", _ns(json=json.dumps(bad))) == 2


def test_add_then_get_step(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "steps", "add", _ns(json=json.dumps(_STEP))) == 0
    assert run_registry_command(config, "steps", "get", _ns(key="s1")) == 0
    assert "g1" in capsys.readouterr().out


def test_step_rejects_empty_goal_id_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_STEP, goal_id="")
    assert run_registry_command(config, "steps", "add", _ns(json=json.dumps(bad))) == 2


# === role-status（P×A 役割のデータ駆動判定）===

from infrastructure.registry_cli import run_role_status


def test_role_status_secretary_when_tables_empty(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_role_status(config) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"role": "secretary", "personalize": False, "accompany": False}


def test_role_status_anego_when_profile_and_active_goal(tmp_path, capsys):
    config = _config(tmp_path)
    run_registry_command(config, "profile", "add", _ns(json=json.dumps(_PROFILE)))
    run_registry_command(config, "goals", "add", _ns(json=json.dumps(_GOAL)))
    capsys.readouterr()  # add の出力を捨てる
    assert run_role_status(config) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"role": "anego", "personalize": True, "accompany": True}


def test_role_status_coach_ignores_profile_of_others(tmp_path, capsys):
    """関係者のプロファイルだけでは P は立たない（subject=principal のみが軸を立てる）。"""
    config = _config(tmp_path)
    other = dict(_PROFILE, id="pf2", subject="u1")
    run_registry_command(config, "profile", "add", _ns(json=json.dumps(other)))
    run_registry_command(config, "goals", "add", _ns(json=json.dumps(_GOAL)))
    capsys.readouterr()
    assert run_role_status(config) == 0
    assert json.loads(capsys.readouterr().out)["role"] == "coach"
