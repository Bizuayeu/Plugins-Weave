"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE）CRUD の CLI ハンドラ。

main.py の subcommand から呼ばれる。値オブジェクトで入力を検証してから永続化する
（決定論的 I/O。何を登録/更新するかの判断は エージェント = 重要度の世界）。

`REGISTRY_SPEC` / `read_json_arg` / `registry_service` は wal_cli と共有する公開名
（旧 private 名の越境 import を解消）。git/sync の DI 組み立ては composition.py に移設済み。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, NamedTuple

from adapters.registry.json_registry_store import JsonRegistryStore
from domain.exceptions import GitSyncError
from domain.registry import (
    Ability,
    Goal,
    Individual,
    Knowledge,
    Profile,
    Step,
    Task,
    derive_role,
)
from infrastructure.composition import build_git, build_sync
from infrastructure.config import Config
from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_FETCH_FAILED, EXIT_OK
from usecases.manage_registry import RegistryService
from usecases.orientation import (
    DEFAULT_HANDOFF_CAP,
    DEFAULT_HANDOFF_LATEST,
    DEFAULT_NOTES_TAIL,
    DEFAULT_TOPIC_WIDTH,
    OrientationService,
)

# list 出力がこの大きさを超えたら警告する（orientation_report_20260809 指定）。
# ハーネスは巨大出力を persisted-output へ退避するため、超過した list は
# 「exit 0 なのにデータがコンテキストに載っていない」沈黙失敗になる。
LIST_WARNING_BYTES = 200 * 1024


class RegistrySpec(NamedTuple):
    """管理表 1 表分の静的仕様（SSoT）。

    path の導出・キーフィールド・値オブジェクトの対応はすべてここから引く
    （`f"{name}_path"` のような文字列組み立てを散らさない）。
    """

    path_attr: str  # Config の path property 名
    key_field: str  # レコードの一意キー
    record_cls: type  # 検証に使う値オブジェクトクラス


# name -> RegistrySpec。wal_cli の kind -> key_field 導出と main.py の subparser 生成も
# ここを SSoT とする（表追加はこの dict に1行足すだけで CRUD/WAL/CLI が揃う）
REGISTRY_SPEC = {
    "individuals": RegistrySpec("individuals_path", "uuid", Individual),
    "tasks": RegistrySpec("tasks_path", "id", Task),
    "knowledge": RegistrySpec("knowledge_path", "id", Knowledge),
    "abilities": RegistrySpec("abilities_path", "id", Ability),
    "profile": RegistrySpec("profile_path", "id", Profile),
    "goals": RegistrySpec("goals_path", "id", Goal),
    "steps": RegistrySpec("steps_path", "id", Step),
}


def registry_service(config: Config, name: str) -> RegistryService:
    """name の管理表に対する RegistryService を組み立てる（wal_cli と共有）。"""
    spec = REGISTRY_SPEC[name]
    return RegistryService(
        JsonRegistryStore(getattr(config, spec.path_attr)), spec.key_field
    )


def run_registry_command(
    config: Config, name: str, action: str, args: Any, sync=None
) -> int:
    spec = REGISTRY_SPEC[name]
    svc = registry_service(config, name)

    if action == "list":
        payload = json.dumps(svc.list(), ensure_ascii=False, indent=2)
        print(payload)
        _warn_if_oversized(name, payload)
        return EXIT_OK

    if action == "get":
        rec = svc.get(args.key)
        if rec is None:
            print(f"not found: {name} {spec.key_field}={args.key}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return EXIT_OK

    if action == "add":
        try:
            raw = read_json_arg(args)
            vo = spec.record_cls.from_dict(raw)  # 値オブジェクトで検証
        except (ValueError, OSError, TypeError, KeyError) as exc:
            # wal_cli.run_wal_append と同一の捕捉タプル（入力不正は exit 2 に統一）。
            # json.JSONDecodeError は ValueError の子なので個別列挙しない
            print(f"invalid {name} record: {exc}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        record = vo.to_dict()
        svc.add_or_update(record)
        _sync_after_change(
            config, name, f"registry: add {name} {record[spec.key_field]}", sync
        )
        print(f"saved {name} {spec.key_field}={record[spec.key_field]}")
        return EXIT_OK

    if action == "remove":
        svc.remove(args.key)
        _sync_after_change(config, name, f"registry: remove {name} {args.key}", sync)
        print(f"removed {name} {spec.key_field}={args.key}")
        return EXIT_OK

    print(f"unknown action: {action}", file=sys.stderr)
    return EXIT_CONFIG_INVALID


def read_json_arg(args: Any) -> dict:
    """--json または --json-file から1レコードの dict を読む（wal_cli と共有）。

    両方未指定は明示メッセージの ValueError——json.loads(None) の TypeError に任せると
    「型エラー」という誤シグナルになるため、入力不正として言語化する
    （CLI 層の捕捉で EXIT_CONFIG_INVALID に翻訳される）。
    """
    if getattr(args, "json_file", None):
        with Path(args.json_file).open(encoding="utf-8") as f:
            text = f.read()
    elif getattr(args, "json", None):
        text = args.json
    else:
        raise ValueError("provide --json or --json-file")
    return json.loads(text)


def _sync_after_change(config: Config, name: str, message: str, sync) -> None:
    """管理表の変更後に git 同期（イベント駆動、R2-3）。

    sync 注入を優先（テスト/外部組み立て）、無ければ config から組み立てる
    （registry_sync_enabled 有効時のみ。無効なら no-op＝ローカルは git に触れない）。
    対象 path は REGISTRY_SPEC から引く（`f"{name}_path"` の文字列組み立てを廃し SSoT 化）。
    """
    service = sync if sync is not None else build_sync(config)
    if service is None:
        return
    path = getattr(config, REGISTRY_SPEC[name].path_attr)
    service.sync([path], message)


def _warn_if_oversized(name: str, payload: str) -> None:
    """list 出力が LIST_WARNING_BYTES 超なら stderr で警告する（fail-open）。

    stdout も exit code も変えない——退行リスクを持ち込まず、「気づけない」だけを潰す
    （run_registry_fetch の空表警告と同型の層3 可観測性）。警告にレコード内容は載せない
    （PII 非出力）ので、サイズと対処だけを言う。
    """
    size = len(payload.encode("utf-8"))
    if size <= LIST_WARNING_BYTES:
        return
    print(
        f"WARNING: {name} list output is {size} bytes (> {LIST_WARNING_BYTES}) — "
        "output this large can be diverted out of the agent's context while the "
        "command still exits 0. Use `orientation` for the startup digest, or "
        "`get --key` for a single record.",
        file=sys.stderr,
    )


def _table_size(config: Config, name: str) -> int:
    """管理表ファイルの実バイト数（不在は 0＝初回起動でも orientation は完走する）。"""
    try:
        return getattr(config, REGISTRY_SPEC[name].path_attr).stat().st_size
    except OSError:
        return 0


def handoff_dir(config: Config) -> Path:
    """申し送りブロックの置き場。`archive/` サブディレクトリが卒業の受け皿になる。"""
    return config.artifacts_path / "handoff"


def _read_handoff_blocks(config: Config, limit: int) -> list[tuple[str, str]]:
    """`artifacts/handoff/*.md` を名前降順 `limit` 件だけ (ファイル名, 本文) で読む。

    非再帰 glob ＝ `handoff/archive/` 配下と非 .md は読まない（**卒業の受け皿の契約**、
    退行テストで固定）。中身は解釈しない（スキーマレス、DESIGN §3.10）——標準化するのは
    置き場と「辞書順ソート可能な命名」だけ。選択規則（名前降順）を UseCase の
    `pick_latest_handoffs` と共有するので、事前絞りは冪等に重なり出力は変わらない。
    不在・空は `[]`（no-op 完走）。読めない 1 ブロックで起動オリエンテーションを
    止めない（fail-open。結果が limit−1 件になるのは許容、stderr で告知する）。
    事前スライス後の 1 件不良は次点で繰り上げ補充しない——補充ループは handoff が
    ほぼ常に 0-3 件の現場に対して過剰（YAGNI）。
    """
    directory = handoff_dir(config)
    try:
        paths = sorted(directory.glob("*.md"), reverse=True)[: max(limit, 0)]
    except OSError:
        return []
    blocks = []
    for path in paths:
        try:
            blocks.append(
                (path.name, path.read_text(encoding="utf-8", errors="replace"))
            )
        except OSError as exc:
            print(f"handoff block unreadable ({path.name}): {exc}", file=sys.stderr)
    return blocks


def _option(args: Any, name: str, default: int) -> int:
    """argparse Namespace から orientation の数値オプションを解決する（未指定のみ既定値）。

    `getattr(...) or default` は falsy な `0` を未指定と同一視するため、最小方向の
    端点指定が最大側の既定に化けていた（絞るためのオプションが全通しの穴になる）。
    `is None` で分岐すれば `0` は UseCase の「非正＝全捨て」ゲートへそのまま届く。
    argparse 側は `default=DEFAULT_*` を持つので CLI 経由では常に値が来る——本ヘルパーは
    `args=None` 直呼び（テスト・プログラム呼び出し）のためのガード。
    """
    value = getattr(args, name, None)
    return default if value is None else value


def run_orientation(config: Config, args: Any = None) -> int:
    """起動時オリエンテーション用の絞り込みダイジェストを stdout に一撃出力する。

    一括 list（7表 1.6MB）はハーネスの出力上限で退避され、データがコンテキストに
    載らないまま exit 0 する沈黙失敗を起こしていた。射影は UseCase の純ロジック、
    ここは stores（REGISTRY_SPEC のキー順＝表追加に自動追従）と実ファイルサイズ・
    handoff ブロックを注入する薄い配線に留める（read-only ゆえ git にも触れない）。
    """
    listers = {name: registry_service(config, name) for name in REGISTRY_SPEC}
    sizes = {name: _table_size(config, name) for name in REGISTRY_SPEC}
    handoff_latest = _option(args, "handoff_latest", DEFAULT_HANDOFF_LATEST)
    print(
        OrientationService(listers, sizes).build(
            handoffs=_read_handoff_blocks(config, handoff_latest),
            notes_tail=_option(args, "notes_tail", DEFAULT_NOTES_TAIL),
            topic_width=_option(args, "topic_width", DEFAULT_TOPIC_WIDTH),
            handoff_latest=handoff_latest,
            handoff_cap=_option(args, "handoff_cap", DEFAULT_HANDOFF_CAP),
            knowledge_category=getattr(args, "knowledge_category", None),
            # 既定 None（全件）ゆえ `_option` は通さない——0 と未指定の区別は
            # getattr の default=None がそのまま担う（knowledge_category と同じ流儀）
            knowledge_latest=getattr(args, "knowledge_latest", None),
        )
    )
    return EXIT_OK


def run_artifacts_sync(config: Config, sync=None) -> int:
    """`artifacts/` 配下を既存 sync 経路で commit & push（新規 git コードを書かない）。

    書き込み CLI は持たない——成果物の構造は秘書の判断（重要度の世界、DESIGN §3.10）。
    ここは「置かれたものを固定ブランチへ送る」決定論だけを担う。registry_sync 無効なら
    no-op exit 0（`_sync_after_change` と同型の後方互換）、`artifacts/` 未作成も no-op
    （存在しない path を `git add` に渡して失敗させない）。
    """
    service = sync if sync is not None else build_sync(config)
    if service is None:
        return EXIT_OK
    directory = config.artifacts_path
    if not directory.exists():
        print(f"artifacts-sync: nothing to sync ({directory} not found)")
        return EXIT_OK
    try:
        result = service.sync([directory], "artifacts: sync")
    except GitSyncError as exc:
        # 申し送りブロックはここを通らないと次枠に届かない＝失敗は伝えるべき事実。
        # スタックトレースを吐かず transient として返す（run_wal_push と同型）
        print(f"artifacts sync failed: {exc}", file=sys.stderr)
        return EXIT_FETCH_FAILED
    print(f"artifacts synced: committed={result.committed} pushed={result.pushed}")
    return EXIT_OK


def run_handoff_archive(config: Config, names: list[str], sync=None) -> int:
    """指名された handoff ブロックを `handoff/archive/` へ mv し、既存 sync で送る（卒業）。

    非再帰読みの契約（`_read_handoff_blocks`）が受け皿なので、移した時点で以後の
    orientation から外れる。**どれを卒業させるかは持たない**——消化（結晶化）を経た
    指名を受けるだけ（判断は重要度の世界、移動は決定論の世界）。名前は `handoff/` 直下の
    ファイル名そのもの（パス成分を含む入力は traversal として拒否、ops-rules §1）。
    全件検証してから全件移動する＝1 件でも落ちれば何も動かない（部分成功を作らない）。
    """
    directory = handoff_dir(config)
    archive = directory / "archive"
    sources = []
    # 重複指名は 1 回に畳む（2 度目の rename を FileNotFoundError で落とさない）
    for name in dict.fromkeys(names):
        if "/" in name or "\\" in name or Path(name).name != name:
            print(f"invalid handoff block name: {name!r}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        if not (directory / name).is_file():
            print(f"handoff block not found: {name}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        if (archive / name).exists():
            # POSIX の rename は黙って上書きする＝卒業済みブロックの消失。事前に止める
            print(f"handoff block already archived: {name}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        sources.append(name)

    archive.mkdir(parents=True, exist_ok=True)
    for name in sources:
        # 同一 FS 内の mv（git 側は rename として拾う＝履歴が切れない）
        (directory / name).rename(archive / name)
    print(f"archived {len(sources)} handoff block(s) to {archive}")
    return run_artifacts_sync(config, sync)


def run_role_status(config: Config) -> int:
    """PROFILE / GOALS から現在の役割（秘書/執事/コーチ/アネゴ）を決定論導出して JSON 1行で emit。

    起動時オリエンテーション（ROUTINE_PROMPT）が叩き、秘書は「今日の自分の顔」を知る。
    判定はコード（derive_role 純関数）、演じ方は SecretaryRole ガイダンス——LLM の役割自称を
    判定根拠にしない（DESIGN §3.11）。
    """
    profiles = registry_service(config, "profile").list()
    goals = registry_service(config, "goals").list()
    print(json.dumps(derive_role(profiles, goals).to_dict(), ensure_ascii=False))
    return EXIT_OK


def run_registry_fetch(config: Config, git=None) -> int:
    """起動時に固定ブランチから管理表を fetch（R2-3、ROUTINE_PROMPT が起動時に呼ぶ）。

    registry_sync 無効なら no-op（exit 0＝ローカル運用は git に触れない）。git 注入は
    テスト用、本番は config から GitCliAdapter を組み立てる。fetch 失敗は
    EXIT_FETCH_FAILED（transient、次回起動で再試行）。
    """
    if not config.registry_sync_enabled:
        return EXIT_OK  # no-op
    service = git if git is not None else build_git(config)
    try:
        service.fetch_checkout(config.registry_branch)
    except GitSyncError as exc:
        # 層3 可観測性: transient を沈黙して握り潰すと「気づけない空表稼働」になる。
        # 失敗の事実に加え、空表で継続＝記憶なし稼働という運用上の含意を警告で明示する
        # （principal への一報は ROUTINE_PROMPT 手順に委譲＝送信責務をコードに持たせない）。
        print(f"registry fetch failed: {exc}", file=sys.stderr)
        print(
            "WARNING: registry-sync is continuing with EMPTY tables — the secretary "
            "runs WITHOUT memory this session (all registry tables and any grants "
            "are unavailable until the next successful fetch). "
            "Treat registry reads as empty and notify the principal that memory is unloaded.",
            file=sys.stderr,
        )
        return EXIT_FETCH_FAILED
    print(f"registry fetched: {config.registry_branch}")
    return EXIT_OK
