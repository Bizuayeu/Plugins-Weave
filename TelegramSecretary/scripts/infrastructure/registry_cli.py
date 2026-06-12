"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE）CRUD の CLI ハンドラ。

main.py の subcommand から呼ばれる。値オブジェクトで入力を検証してから永続化する
（決定論的 I/O。何を登録/更新するかの判断は エージェント = 重要度の世界）。

`REGISTRY_SPEC` / `read_json_arg` / `registry_service` は wal_cli と共有する公開名
（旧 private 名の越境 import を解消）。git/sync の DI 組み立ては composition.py に移設済み。
"""
from __future__ import annotations

import json
import sys
from typing import Any, NamedTuple, Type

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


class RegistrySpec(NamedTuple):
    """管理表 1 表分の静的仕様（SSoT）。

    path の導出・キーフィールド・値オブジェクトの対応はすべてここから引く
    （`f"{name}_path"` のような文字列組み立てを散らさない）。
    """

    path_attr: str  # Config の path property 名
    key_field: str  # レコードの一意キー
    record_cls: Type  # 検証に使う値オブジェクトクラス


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


def run_registry_command(config: Config, name: str, action: str, args: Any, sync=None) -> int:
    spec = REGISTRY_SPEC[name]
    svc = registry_service(config, name)

    if action == "list":
        print(json.dumps(svc.list(), ensure_ascii=False, indent=2))
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
        _sync_after_change(config, name, f"registry: add {name} {record[spec.key_field]}", sync)
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
        with open(args.json_file, encoding="utf-8") as f:
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
