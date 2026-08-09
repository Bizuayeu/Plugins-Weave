from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest
from domain.authorization import AuthorizedChats
from domain.exceptions import GitSyncError
from infrastructure.config import Config
from infrastructure.registry_cli import run_registry_command, run_registry_fetch
from tests.usecases.fakes import FakeGitSync
from usecases.registry_sync import RegistrySyncService


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
    "uuid": "u1",
    "display_name": "yamada",
    "role": "associate",
    "status": "active",
    "created_at": "t",
    "updated_at": "t",
}


def test_add_then_get_individual(tmp_path, capsys):
    config = _config(tmp_path)
    assert (
        run_registry_command(
            config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))
        )
        == 0
    )
    assert run_registry_command(config, "individuals", "get", _ns(key="u1")) == 0
    assert "yamada" in capsys.readouterr().out


def test_add_invalid_role_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_INDIVIDUAL, role="boss")
    assert (
        run_registry_command(config, "individuals", "add", _ns(json=json.dumps(bad)))
        == 2
    )


def test_list_empty_prints_empty_array(tmp_path, capsys):
    config = _config(tmp_path)
    assert run_registry_command(config, "individuals", "list", _ns()) == 0
    assert capsys.readouterr().out.strip() == "[]"


def test_get_missing_returns_2(tmp_path):
    config = _config(tmp_path)
    assert run_registry_command(config, "tasks", "get", _ns(key="zzz")) == 2


def test_remove_individual(tmp_path):
    config = _config(tmp_path)
    run_registry_command(
        config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))
    )
    assert run_registry_command(config, "individuals", "remove", _ns(key="u1")) == 0
    assert run_registry_command(config, "individuals", "get", _ns(key="u1")) == 2


def test_add_persists_to_correct_path(tmp_path):
    config = _config(tmp_path)
    run_registry_command(
        config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))
    )
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
    run_registry_command(
        config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))
    )
    assert (reg / "individuals" / "INDIVIDUALS.json").exists()
    assert not (state / "individuals").exists()


# === R2-3: イベント駆動 sync（DI） ===


def test_add_triggers_sync_when_provided(tmp_path):
    """sync 注入時、add 成功後に sync が走る（commit→push）。"""
    config = _config(tmp_path)
    git = FakeGitSync()
    run_registry_command(
        config,
        "individuals",
        "add",
        _ns(json=json.dumps(_INDIVIDUAL)),
        sync=RegistrySyncService(git),
    )
    assert len(git.commit_calls) == 1
    assert git.push_calls == 1


def test_remove_triggers_sync_when_provided(tmp_path):
    config = _config(tmp_path)
    run_registry_command(
        config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))
    )
    git = FakeGitSync()
    run_registry_command(
        config,
        "individuals",
        "remove",
        _ns(key="u1"),
        sync=RegistrySyncService(git),
    )
    assert len(git.commit_calls) == 1


def test_list_does_not_trigger_sync(tmp_path):
    """list は読み取りゆえ sync しない。"""
    config = _config(tmp_path)
    git = FakeGitSync()
    run_registry_command(
        config, "individuals", "list", _ns(), sync=RegistrySyncService(git)
    )
    assert git.commit_calls == []


def test_no_sync_when_not_provided(tmp_path):
    """sync 未注入なら従来通り（後方互換、git に触れない）。"""
    config = _config(tmp_path)
    assert (
        run_registry_command(
            config, "individuals", "add", _ns(json=json.dumps(_INDIVIDUAL))
        )
        == 0
    )


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

    assert (
        run_registry_fetch(_config(tmp_path), git=FakeGitSync()) == 0
    )  # no-op（無効）
    assert "empty" not in capsys.readouterr().err.lower()


# === abilities（4 表目、registry 同格・WAL 対象）===


_ABILITY = {
    "id": "precognitive-viewer",
    "name": "三位占術鑑定",
    "created_at": "t",
    "updated_at": "t",
}


def test_add_then_get_ability(tmp_path, capsys):
    config = _config(tmp_path)
    assert (
        run_registry_command(config, "abilities", "add", _ns(json=json.dumps(_ABILITY)))
        == 0
    )
    assert (
        run_registry_command(config, "abilities", "get", _ns(key="precognitive-viewer"))
        == 0
    )
    assert "precognitive-viewer" in capsys.readouterr().out


def test_ability_persists_to_abilities_path(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "abilities", "add", _ns(json=json.dumps(_ABILITY)))
    assert config.abilities_path.exists()


def test_ability_rejects_empty_name_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_ABILITY, name="")
    assert (
        run_registry_command(config, "abilities", "add", _ns(json=json.dumps(bad))) == 2
    )


# === P/A 軸 3 表（PROFILE / GOALS / STEPS、registry 同格・WAL 対象）===


_PROFILE = {
    "id": "pf1",
    "subject": "principal",
    "method": "mbti",
    "content": "INTJ",
    "created_at": "t",
    "updated_at": "t",
}
_GOAL = {
    "id": "g1",
    "title": "半年で貯蓄30万円",
    "category": "money",
    "status": "active",
    "created_at": "t",
    "updated_at": "t",
}
_STEP = {
    "id": "s1",
    "goal_id": "g1",
    "title": "固定費一覧を作る",
    "created_at": "t",
    "updated_at": "t",
}


def test_add_then_get_profile(tmp_path, capsys):
    config = _config(tmp_path)
    assert (
        run_registry_command(config, "profile", "add", _ns(json=json.dumps(_PROFILE)))
        == 0
    )
    assert run_registry_command(config, "profile", "get", _ns(key="pf1")) == 0
    assert "principal" in capsys.readouterr().out


def test_profile_persists_to_profile_path(tmp_path):
    config = _config(tmp_path)
    run_registry_command(config, "profile", "add", _ns(json=json.dumps(_PROFILE)))
    assert config.profile_path.exists()


def test_profile_rejects_invalid_method_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_PROFILE, method="palm_reading")
    assert (
        run_registry_command(config, "profile", "add", _ns(json=json.dumps(bad))) == 2
    )


def test_add_then_get_goal(tmp_path, capsys):
    config = _config(tmp_path)
    assert (
        run_registry_command(config, "goals", "add", _ns(json=json.dumps(_GOAL))) == 0
    )
    assert run_registry_command(config, "goals", "get", _ns(key="g1")) == 0
    assert "money" in capsys.readouterr().out


def test_goal_rejects_invalid_category_returns_2(tmp_path):
    config = _config(tmp_path)
    bad = dict(_GOAL, category="gambling")
    assert run_registry_command(config, "goals", "add", _ns(json=json.dumps(bad))) == 2


def test_add_then_get_step(tmp_path, capsys):
    config = _config(tmp_path)
    assert (
        run_registry_command(config, "steps", "add", _ns(json=json.dumps(_STEP))) == 0
    )
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


# === orientation（起動時ダイジェスト）と list サイズ警告 ===

from infrastructure.registry_cli import (
    LIST_WARNING_BYTES,
    ORIENTATION_WARNING_BYTES,
    run_orientation,
)
from usecases.orientation import (
    DEFAULT_HANDOFF_CAP,
    DEFAULT_HANDOFF_LATEST,
    DEFAULT_NOTES_TAIL,
)

_TASK = {
    "id": "T-001",
    "title": "見積を送る",
    "status": "in_progress",
    "priority": "high",
    "requester": "principal",
    "notes": "HEAD_MARKER" + "x" * 165_000 + "TAIL_MARKER",
    "created_at": "t",
    "updated_at": "t",
}
_KNOWLEDGE = {
    "id": "K-001",
    "topic": "申し送りの置き場",
    # category は許可集合（domain._KNOWLEDGE_CATEGORIES）の値のみ通る（欠落は exit 2）
    "category": "harness",
    "content": "CONTENT_MARKER" + "c" * 1_000,
    "created_at": "t",
    "updated_at": "t",
}


def test_orientation_completes_with_zero_counts_when_tables_absent(tmp_path, capsys):
    """表ファイルが 1 つも無い初回起動でも 0 件・0 バイトで完走する（fail-open）。"""
    config = _config(tmp_path)
    assert run_orientation(config, _ns()) == 0
    out = capsys.readouterr().out
    assert "tasks: 0 records, 0 bytes" in out
    assert "## role" in out


def test_orientation_counts_match_actual_file_sizes(tmp_path, capsys):
    config = _config(tmp_path)
    run_registry_command(config, "tasks", "add", _ns(json=json.dumps(_TASK)))
    capsys.readouterr()
    assert run_orientation(config, _ns()) == 0
    out = capsys.readouterr().out
    assert f"tasks: 1 records, {config.tasks_path.stat().st_size} bytes" in out


def test_orientation_output_is_bounded_and_drops_bulk_fields(tmp_path, capsys):
    """実ファイル経由でも digest は notes 長・content 長に引きずられない（沈黙失敗の根治）。"""
    config = _config(tmp_path)
    run_registry_command(config, "tasks", "add", _ns(json=json.dumps(_TASK)))
    run_registry_command(config, "knowledge", "add", _ns(json=json.dumps(_KNOWLEDGE)))
    capsys.readouterr()
    assert run_orientation(config, _ns()) == 0
    out = capsys.readouterr().out
    assert "TAIL_MARKER" in out and "HEAD_MARKER" not in out
    assert "CONTENT_MARKER" not in out
    assert len(out) < 10_000


def test_orientation_options_override_defaults(tmp_path, capsys):
    config = _config(tmp_path)
    run_registry_command(config, "tasks", "add", _ns(json=json.dumps(_TASK)))
    run_registry_command(
        config,
        "knowledge",
        "add",
        _ns(json=json.dumps(dict(_KNOWLEDGE, topic="z" * 300))),
    )
    capsys.readouterr()
    assert run_orientation(config, _ns(notes_tail=50, topic_width=10)) == 0
    out = capsys.readouterr().out
    assert "z" * 11 not in out
    assert len(out) < 3_000


def test_orientation_knowledge_category_option_is_wired_through(tmp_path, capsys):
    """`--knowledge-category` が CLI から UseCase まで通る（絞りの実配線）。"""
    config = _config(tmp_path)
    for kid, category, topic in (
        ("K-001", "harness", "OPS_TOPIC"),
        ("K-002", "business", "BILLING_TOPIC"),
    ):
        run_registry_command(
            config,
            "knowledge",
            "add",
            _ns(
                json=json.dumps(
                    dict(_KNOWLEDGE, id=kid, category=category, topic=topic)
                )
            ),
        )
    capsys.readouterr()
    assert run_orientation(config, _ns(knowledge_category="harness")) == 0
    out = capsys.readouterr().out
    assert "1 of 2 records, category=harness" in out
    assert "OPS_TOPIC" in out
    assert "BILLING_TOPIC" not in out


def test_orientation_without_category_option_is_unchanged(tmp_path, capsys):
    """引数未指定（属性そのものが無い呼び出しを含む）は従来出力（後方互換）。"""
    config = _config(tmp_path)
    run_registry_command(config, "knowledge", "add", _ns(json=json.dumps(_KNOWLEDGE)))
    capsys.readouterr()
    assert run_orientation(config, _ns()) == 0
    assert "## knowledge (1 records, index: id | topic)" in capsys.readouterr().out


def test_orientation_knowledge_latest_option_is_wired_through(tmp_path, capsys):
    """`--knowledge-latest` が CLI から UseCase まで通る（新しい順の実配線）。"""
    config = _config(tmp_path)
    for kid, topic in (("K-001", "OLD_TOPIC"), ("K-002", "NEW_TOPIC")):
        run_registry_command(
            config,
            "knowledge",
            "add",
            _ns(json=json.dumps(dict(_KNOWLEDGE, id=kid, topic=topic))),
        )
    capsys.readouterr()
    assert run_orientation(config, _ns(knowledge_latest=1)) == 0
    out = capsys.readouterr().out
    assert "latest 1 of 2 records" in out
    assert "NEW_TOPIC" in out
    assert "OLD_TOPIC" not in out


def test_zero_knowledge_latest_is_not_read_as_unset(tmp_path, capsys):
    """`--knowledge-latest 0` は未指定（None＝全件）へ逆転せず、0 件として届く。"""
    config = _config(tmp_path)
    run_registry_command(config, "knowledge", "add", _ns(json=json.dumps(_KNOWLEDGE)))
    capsys.readouterr()
    assert run_orientation(config, _ns(knowledge_latest=0)) == 0
    out = capsys.readouterr().out
    assert "latest 0 of 1 records" in out
    assert "K-001 |" not in out


# === 0 指定は「全捨て」の端点として通る（falsy 罠の封じ、v1.7.0 Stage 1） ===


def test_zero_notes_tail_drops_notes_instead_of_passing_them_through(tmp_path, capsys):
    """`--notes-tail 0` は既定 4000 へ逆転せず全捨てに届く。

    `getattr(...) or DEFAULT` は 0 を未指定と同一視するため、最小方向の端点を
    指定したはずが最大側の既定に化けていた（絞るためのオプションが全通しの穴になる）。
    """
    config = _config(tmp_path)
    run_registry_command(config, "tasks", "add", _ns(json=json.dumps(_TASK)))
    capsys.readouterr()
    assert run_orientation(config, _ns(notes_tail=0)) == 0
    out = capsys.readouterr().out
    assert "last 0 bytes" in out
    assert "TAIL_MARKER" not in out


def test_zero_topic_width_leaves_only_the_marker_in_the_knowledge_index(
    tmp_path, capsys
):
    """`--topic-width 0` も同じ端点規約——索引に残るのは id と切り取りマーカーだけ。"""
    config = _config(tmp_path)
    run_registry_command(config, "knowledge", "add", _ns(json=json.dumps(_KNOWLEDGE)))
    capsys.readouterr()
    assert run_orientation(config, _ns(topic_width=0)) == 0
    out = capsys.readouterr().out
    assert "K-001 | …" in out
    assert "申し送りの置き場" not in out


def test_orientation_without_args_still_uses_the_defaults(tmp_path, capsys):
    """`args=None` の直呼びは従来どおり既定値で完走する（後方互換の担保）。

    `is None` 判定へ移しても「未指定＝既定」は変わらない——0 と未指定の区別が
    付いただけであることを、引数オブジェクトそのものが無い経路で固定する。
    """
    config = _config(tmp_path)
    run_registry_command(config, "tasks", "add", _ns(json=json.dumps(_TASK)))
    capsys.readouterr()
    assert run_orientation(config, None) == 0
    out = capsys.readouterr().out
    assert f"last {DEFAULT_NOTES_TAIL} bytes" in out
    assert "TAIL_MARKER" in out
    assert f"latest {DEFAULT_HANDOFF_LATEST}, cap {DEFAULT_HANDOFF_CAP} bytes" in out


def test_orientation_does_not_trigger_sync(tmp_path):
    """orientation は読み取り専用（git に触れない）。"""
    config = _config(tmp_path, sync=True)
    assert run_orientation(config, _ns()) == 0


def test_list_warns_when_output_exceeds_threshold(tmp_path, capsys):
    """200KB 超の list は stderr で警告（沈黙→声）。stdout と exit 0 は不変＝fail-open。"""
    config = _config(tmp_path)
    bulky = dict(_KNOWLEDGE, content="SECRET_CONTENT" + "c" * 220_000)
    run_registry_command(config, "knowledge", "add", _ns(json=json.dumps(bulky)))
    capsys.readouterr()
    assert run_registry_command(config, "knowledge", "list", _ns()) == 0
    captured = capsys.readouterr()
    assert "SECRET_CONTENT" in captured.out  # 出力そのものは削らない
    assert "WARNING" in captured.err
    assert "orientation" in captured.err  # どう直すかが分かる
    assert "SECRET_CONTENT" not in captured.err  # 警告にレコード内容は載せない


def test_list_below_threshold_is_silent(tmp_path, capsys):
    config = _config(tmp_path)
    run_registry_command(config, "knowledge", "add", _ns(json=json.dumps(_KNOWLEDGE)))
    capsys.readouterr()
    assert run_registry_command(config, "knowledge", "list", _ns()) == 0
    assert "WARNING" not in capsys.readouterr().err
    assert LIST_WARNING_BYTES == 200 * 1024  # 閾値は orientation_report_20260809 指定


# === orientation 出力サイズの自己申告（v1.8.0 Stage 2） ===

_SNAPSHOT_TASK = dict(_TASK, notes="NOTE_A")


# v1.7.0 の run_orientation が既定オプションで stdout へ出した全文（末尾の改行は print 由来）。
# 計器（stderr）を足しても **stdout は 1 バイトも動かない** ことを固定する——起動時
# オリエンテーションは秘書が毎枠読む契約面であり、計器の混入は digest そのものの汚染になる。
# counts の実バイト数だけは改行変換で OS 依存（Windows は CRLF）なので stat() から差し込む。
# f-string 内の role 行の波括弧は二重化（表示は 1 重）。
def _expected_default_stdout(config: Config) -> str:
    return f"""# orientation

## role
{{"role": "secretary", "personalize": false, "accompany": false}}

## counts
individuals: 0 records, 0 bytes
tasks: 1 records, {config.tasks_path.stat().st_size} bytes
knowledge: 1 records, {config.knowledge_path.stat().st_size} bytes
abilities: 0 records, 0 bytes
profile: 0 records, 0 bytes
goals: 0 records, 0 bytes
steps: 0 records, 0 bytes

## individuals (0 records, full)
[]

## tasks (1 records, summary: id | status | priority | due_date | title)
T-001 | in_progress | high | - | 見積を送る

## tasks.notes (active only, last 4000 bytes)
### T-001
NOTE_A

## knowledge (1 records, index: id | topic)
K-001 | 申し送りの置き場

## abilities (0 records, full)
[]

## profile (0 records, full)
[]

## goals (0 records, full)
[]

## steps (0 records, full)
[]

## handoff (0 blocks, latest 3, cap 8000 bytes)

"""


def _add_snapshot_records(config: Config) -> None:
    run_registry_command(config, "tasks", "add", _ns(json=json.dumps(_SNAPSHOT_TASK)))
    run_registry_command(config, "knowledge", "add", _ns(json=json.dumps(_KNOWLEDGE)))


def test_orientation_always_reports_its_size_on_stderr(tmp_path, capsys):
    """digest の総バイトを毎回 stderr へ 1 行申告する（閾値未満でも黙らない）。

    「exit 0 なのにデータがコンテキストに載っていない」は自己観測できないと直せない
    ——サイズが毎枠見え続けることが、以後の絞り校正の自走材料になる。
    """
    config = _config(tmp_path)
    _add_snapshot_records(config)
    capsys.readouterr()
    assert run_orientation(config, _ns()) == 0
    captured = capsys.readouterr()
    digest_bytes = len(captured.out.encode("utf-8")) - 1  # print が足す改行を除く
    assert f"orientation digest: {digest_bytes} bytes" in captured.err


def test_orientation_warns_and_names_narrowing_options_when_oversized(tmp_path, capsys):
    """閾値超は persisted 退避の可能性と、実在する絞りオプションの名指しを添える。"""
    config = _config(tmp_path)
    run_registry_command(config, "tasks", "add", _ns(json=json.dumps(_TASK)))
    capsys.readouterr()
    assert run_orientation(config, _ns(notes_tail=30_000)) == 0
    captured = capsys.readouterr()
    assert len(captured.out.encode("utf-8")) > ORIENTATION_WARNING_BYTES  # 前提の確認
    assert "WARNING" in captured.err
    for option in (
        "--knowledge-latest",
        "--notes-tail",
        "--handoff-latest",
        "--handoff-cap",
    ):
        assert option in captured.err
    assert (
        "TAIL_MARKER" not in captured.err
    )  # 警告にレコード内容は載せない（PII 非出力）


def test_orientation_below_threshold_reports_size_without_warning(tmp_path, capsys):
    """小さい出力では常時 1 行だけ——計器は鳴るが警報にはならない。"""
    config = _config(tmp_path)
    _add_snapshot_records(config)
    capsys.readouterr()
    assert run_orientation(config, _ns()) == 0
    captured = capsys.readouterr()
    assert "orientation digest:" in captured.err
    assert "WARNING" not in captured.err
    # 閾値は実測境界（20KB 台は載った／45.8KB は落ちた）の安全側下限＝仮置き
    assert ORIENTATION_WARNING_BYTES == 25 * 1024


def test_orientation_stdout_is_byte_identical_to_v170(tmp_path, capsys):
    """計器は stderr のみ。stdout（digest 本文）は v1.7.0 と byte 同一。"""
    config = _config(tmp_path)
    _add_snapshot_records(config)
    capsys.readouterr()
    assert run_orientation(config, _ns()) == 0
    assert capsys.readouterr().out == _expected_default_stdout(config)


# === handoff ブロック（申し送りの置き場）と artifacts-sync ===

from infrastructure.registry_cli import (
    REGISTRY_SPEC,
    registry_service,
    run_artifacts_sync,
)
from usecases.orientation import OrientationService


def _write_handoff(config: Config, name: str, body: str) -> Path:
    path = config.artifacts_path / "handoff" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8", newline="\n")
    return path


def test_orientation_reads_latest_handoff_blocks(tmp_path, capsys):
    """置いたブロックの本文が次の orientation に載る（枠をまたぐ申し送りの経路）。"""
    config = _config(tmp_path)
    for day, body in (("07", "OLDEST"), ("08", "MIDDLE"), ("09", "NEWEST")):
        _write_handoff(config, f"202608{day}T000000Z_s.md", f"{body}_BODY")
    assert run_orientation(config, _ns(handoff_latest=2)) == 0
    out = capsys.readouterr().out
    assert "2 blocks" in out
    assert "NEWEST_BODY" in out and "MIDDLE_BODY" in out
    assert "OLDEST_BODY" not in out  # 降順 N 件のみ


def test_orientation_handoff_body_is_capped(tmp_path, capsys):
    config = _config(tmp_path)
    _write_handoff(config, "20260809T000000Z_s.md", "HEAD" + "z" * 20_000)
    assert run_orientation(config, _ns(handoff_cap=100)) == 0
    out = capsys.readouterr().out
    assert "HEAD" in out
    assert "z" * 200 not in out


def test_orientation_completes_when_handoff_dir_absent(tmp_path, capsys):
    """handoff ディレクトリ不在でも no-op 完走（0 blocks）。"""
    config = _config(tmp_path)
    assert run_orientation(config, _ns()) == 0
    assert "0 blocks" in capsys.readouterr().out


def test_orientation_completes_when_handoff_dir_empty(tmp_path, capsys):
    config = _config(tmp_path)
    (config.artifacts_path / "handoff").mkdir(parents=True)
    assert run_orientation(config, _ns()) == 0
    assert "0 blocks" in capsys.readouterr().out


# === handoff の有界読みと「archive/ は読まれない」契約（v1.6.0 Stage 1） ===


def _count_handoff_reads(monkeypatch, config: Config) -> list[str]:
    """handoff ディレクトリ直下の read_text を記録するカウンタを仕込む（open 回数の観測）。"""
    opened: list[str] = []
    original = Path.read_text
    handoff_dir = config.artifacts_path / "handoff"

    def counting_read_text(self: Path, *args, **kwargs):
        if self.parent == handoff_dir:
            opened.append(self.name)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", counting_read_text)
    return opened


def test_orientation_opens_only_the_latest_handoff_blocks(tmp_path, monkeypatch):
    """10 ブロック置いても latest=3 なら open は 3 回だけ（読みは表示件数に有界）。

    全件 open は「読んだ末に捨てる」＝ブロックが溜まるほど起動が遅くなる経路だった。
    選択規則（名前降順）は UseCase と共有し、読み側の事前絞りは冪等に重なる。
    """
    config = _config(tmp_path)
    for i in range(10):
        _write_handoff(config, f"202608{i:02d}T000000Z_s.md", f"BODY{i}")
    opened = _count_handoff_reads(monkeypatch, config)
    assert run_orientation(config, _ns(handoff_latest=3)) == 0
    assert opened == [
        "20260809T000000Z_s.md",
        "20260808T000000Z_s.md",
        "20260807T000000Z_s.md",
    ]


def test_zero_handoff_latest_opens_no_block_file_at_all(tmp_path, monkeypatch, capsys):
    """`--handoff-latest 0` は既定 3 へ逆転せず、ファイルを 1 つも open しない。

    端点が既定に化けると「載せない」指定が「3 件読んで載せる」に反転する——
    有界読み（表示件数に読みを合わせる契約）の下端をここで固定する。
    """
    config = _config(tmp_path)
    for i in range(3):
        _write_handoff(config, f"202608{i:02d}T000000Z_s.md", f"BODY{i}")
    opened = _count_handoff_reads(monkeypatch, config)
    assert run_orientation(config, _ns(handoff_latest=0)) == 0
    out = capsys.readouterr().out
    assert opened == []
    assert "## handoff (0 blocks" in out
    assert "BODY" not in out


def test_zero_handoff_cap_drops_block_bodies_but_keeps_their_names(tmp_path, capsys):
    """`--handoff-cap 0` も既定 8000 へ逆転せず、本文を全捨てする（端点 4 つ目）。

    ブロック名は残す——「申し送りが無い」のではなく「載せない指定をした」ことが
    読み手（秘書）に分かる形で下端を締める。
    """
    config = _config(tmp_path)
    _write_handoff(config, "20260809T000000Z_s.md", "BLOCK_BODY")
    assert run_orientation(config, _ns(handoff_cap=0)) == 0
    out = capsys.readouterr().out
    assert "cap 0 bytes" in out
    assert "### 20260809T000000Z_s.md" in out
    assert "BLOCK_BODY" not in out


def test_bounded_handoff_read_yields_same_digest_as_full_read(tmp_path, capsys):
    """事前絞りを入れても digest は全件読み実装と同一（内部整形＝出力不変）。"""
    config = _config(tmp_path)
    for i in range(10):
        _write_handoff(config, f"202608{i:02d}T000000Z_s.md", f"BODY{i}")
    assert run_orientation(config, _ns(handoff_latest=3)) == 0
    bounded = capsys.readouterr().out

    all_blocks = [
        (path.name, path.read_text(encoding="utf-8"))
        for path in sorted((config.artifacts_path / "handoff").glob("*.md"))
    ]
    full_read = OrientationService(
        {name: registry_service(config, name) for name in REGISTRY_SPEC},
        dict.fromkeys(REGISTRY_SPEC, 0),
    ).build(handoffs=all_blocks, handoff_latest=3)
    assert bounded == full_read + "\n"  # print が付ける改行のみの差


def test_orientation_ignores_archive_subdir_and_non_md_files(tmp_path, capsys):
    """卒業の受け皿の契約: `handoff/archive/` 配下と非 .md は orientation に載らない。

    非再帰 glob("*.md") の暗黙挙動をテストで契約に昇格させる——ここが崩れると
    `handoff-archive` で卒業させたブロックが digest に居座り続ける。
    """
    config = _config(tmp_path)
    _write_handoff(config, "20260809T000000Z_s.md", "LIVE_BODY")
    _write_handoff(config, "memo.txt", "MEMO_BODY")
    archived = config.artifacts_path / "handoff" / "archive" / "20260801T000000Z_s.md"
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_text("ARCHIVED_BODY", encoding="utf-8", newline="\n")

    assert run_orientation(config, _ns()) == 0
    out = capsys.readouterr().out
    assert "LIVE_BODY" in out
    assert "ARCHIVED_BODY" not in out
    assert "MEMO_BODY" not in out
    assert "1 blocks" in out


def test_artifacts_sync_syncs_artifacts_dir(tmp_path, capsys):
    """artifacts-sync は既存 sync 経路（RegistrySyncService）へ artifacts/ を渡すだけ。"""
    config = _config(tmp_path, sync=True)
    _write_handoff(config, "20260809T000000Z_s.md", "body")
    git = FakeGitSync()
    assert run_artifacts_sync(config, sync=RegistrySyncService(git)) == 0
    paths, _message = git.commit_calls[0]
    assert paths == [config.artifacts_path]
    assert git.push_calls == 1


def test_artifacts_sync_noop_when_registry_sync_disabled(tmp_path):
    """registry_sync 無効ならローカル運用（git に触れず exit 0、後方互換）。"""
    config = _config(tmp_path)
    _write_handoff(config, "20260809T000000Z_s.md", "body")
    assert run_artifacts_sync(config) == 0


def test_artifacts_sync_reports_git_failure_without_traceback(tmp_path, capsys):
    """git 失敗は transient として返す（申し送りが届かない事実は伝える、クラッシュはしない）。"""

    class _FailingSync:
        def sync(self, paths, message):
            raise GitSyncError("simulated commit failure")

    config = _config(tmp_path, sync=True)
    _write_handoff(config, "20260809T000000Z_s.md", "body")
    assert run_artifacts_sync(config, sync=_FailingSync()) == 1
    assert "artifacts sync failed" in capsys.readouterr().err


def test_artifacts_sync_noop_when_artifacts_dir_absent(tmp_path):
    """成果物が 1 つも無い環境で git add の失敗を作らない（no-op exit 0）。"""
    config = _config(tmp_path, sync=True)
    git = FakeGitSync()
    assert run_artifacts_sync(config, sync=RegistrySyncService(git)) == 0
    assert git.commit_calls == []


# === handoff-archive（卒業の決定論操作、v1.6.0 Stage 3） ===

from infrastructure.registry_cli import run_handoff_archive


def test_handoff_archive_moves_named_blocks_out_of_the_digest(tmp_path, capsys):
    """指名ブロックは archive/ へ移り、次の orientation から消える（残りは従来どおり）。"""
    config = _config(tmp_path)
    for day, body in (("07", "OLD"), ("08", "MID"), ("09", "NEW")):
        _write_handoff(config, f"202608{day}T000000Z_s.md", f"{body}_BODY")

    assert (
        run_handoff_archive(config, ["20260807T000000Z_s.md", "20260808T000000Z_s.md"])
        == 0
    )
    capsys.readouterr()

    handoff = config.artifacts_path / "handoff"
    assert sorted(p.name for p in handoff.glob("*.md")) == ["20260809T000000Z_s.md"]
    assert sorted(p.name for p in (handoff / "archive").glob("*.md")) == [
        "20260807T000000Z_s.md",
        "20260808T000000Z_s.md",
    ]

    assert run_orientation(config, _ns()) == 0
    out = capsys.readouterr().out
    assert "NEW_BODY" in out
    assert "OLD_BODY" not in out and "MID_BODY" not in out
    assert "1 blocks" in out


@pytest.mark.parametrize(
    "name",
    [
        "../secrets.md",
        "sub/20260809T000000Z_s.md",
        "sub\\20260809T000000Z_s.md",
        "/etc/passwd",
        "C:\\Windows\\system.ini",
    ],
)
def test_handoff_archive_rejects_names_with_path_components(tmp_path, name, capsys):
    """パス成分を含む名前は exit 2（traversal 封じ＝完全一致主義、ops-rules §1）。"""
    config = _config(tmp_path)
    _write_handoff(config, "20260809T000000Z_s.md", "LIVE")
    assert run_handoff_archive(config, [name]) == 2
    assert "invalid handoff block name" in capsys.readouterr().err
    assert not (config.artifacts_path / "handoff" / "archive").exists()


def test_handoff_archive_rejects_missing_block_and_moves_nothing(tmp_path, capsys):
    """1 件でも不在なら何も動かさない（全件検証→全件移動＝部分成功を作らない）。"""
    config = _config(tmp_path)
    _write_handoff(config, "20260809T000000Z_s.md", "LIVE")
    assert (
        run_handoff_archive(config, ["20260809T000000Z_s.md", "20260801T000000Z_s.md"])
        == 2
    )
    assert "not found" in capsys.readouterr().err
    handoff = config.artifacts_path / "handoff"
    assert (handoff / "20260809T000000Z_s.md").exists()
    assert not (handoff / "archive").exists()


def test_handoff_archive_syncs_artifacts_dir(tmp_path, capsys):
    """mv 後は既存 sync 経路へ artifacts/ を渡すだけ（rename は git add <dir> が拾う）。"""
    config = _config(tmp_path, sync=True)
    _write_handoff(config, "20260809T000000Z_s.md", "body")
    git = FakeGitSync()
    assert (
        run_handoff_archive(
            config, ["20260809T000000Z_s.md"], sync=RegistrySyncService(git)
        )
        == 0
    )
    paths, _message = git.commit_calls[0]
    assert paths == [config.artifacts_path]
    assert git.push_calls == 1


def test_handoff_archive_moves_without_git_when_sync_disabled(tmp_path, capsys):
    """registry_sync 無効なら mv のみで exit 0（`_sync_after_change` と同型の後方互換）。"""
    config = _config(tmp_path)
    _write_handoff(config, "20260809T000000Z_s.md", "body")
    assert run_handoff_archive(config, ["20260809T000000Z_s.md"]) == 0
    handoff = config.artifacts_path / "handoff"
    assert (handoff / "archive" / "20260809T000000Z_s.md").exists()
    assert not (handoff / "20260809T000000Z_s.md").exists()
