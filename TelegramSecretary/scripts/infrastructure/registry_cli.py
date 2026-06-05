"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE）CRUD の CLI ハンドラ。

main.py の subcommand から呼ばれる。値オブジェクトで入力を検証してから永続化する
（決定論的 I/O。何を登録/更新するかの判断は エージェント = 重要度の世界）。
"""
from __future__ import annotations

import json
import sys
from typing import Any

from adapters.registry.json_registry_store import JsonRegistryStore
from domain.exceptions import GitSyncError
from domain.registry import Ability, Individual, Knowledge, Task
from infrastructure.config import Config
from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_FETCH_FAILED, EXIT_OK
from usecases.manage_registry import RegistryService

# name -> (Config の path property 名, キーフィールド, 値オブジェクトクラス)
_REGISTRY_SPEC = {
    "individuals": ("individuals_path", "uuid", Individual),
    "tasks": ("tasks_path", "id", Task),
    "knowledge": ("knowledge_path", "id", Knowledge),
    "abilities": ("abilities_path", "id", Ability),
}


def _service(config: Config, name: str) -> RegistryService:
    path_attr, key_field, _ = _REGISTRY_SPEC[name]
    return RegistryService(JsonRegistryStore(getattr(config, path_attr)), key_field)


def run_registry_command(config: Config, name: str, action: str, args: Any, sync=None) -> int:
    key_field, vo_cls = _REGISTRY_SPEC[name][1], _REGISTRY_SPEC[name][2]
    svc = _service(config, name)

    if action == "list":
        print(json.dumps(svc.list(), ensure_ascii=False, indent=2))
        return EXIT_OK

    if action == "get":
        rec = svc.get(args.key)
        if rec is None:
            print(f"not found: {name} {key_field}={args.key}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        print(json.dumps(rec, ensure_ascii=False, indent=2))
        return EXIT_OK

    if action == "add":
        try:
            raw = _read_json_arg(args)
            vo = vo_cls.from_dict(raw)  # 値オブジェクトで検証
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            print(f"invalid {name} record: {exc}", file=sys.stderr)
            return EXIT_CONFIG_INVALID
        record = vo.to_dict()
        svc.add_or_update(record)
        _sync_after_change(config, name, f"registry: add {name} {record[key_field]}", sync)
        print(f"saved {name} {key_field}={record[key_field]}")
        return EXIT_OK

    if action == "remove":
        svc.remove(args.key)
        _sync_after_change(config, name, f"registry: remove {name} {args.key}", sync)
        print(f"removed {name} {key_field}={args.key}")
        return EXIT_OK

    print(f"unknown action: {action}", file=sys.stderr)
    return EXIT_CONFIG_INVALID


def _read_json_arg(args: Any) -> dict:
    """--json または --json-file から1レコードの dict を読む。"""
    if getattr(args, "json_file", None):
        with open(args.json_file, encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.json
    return json.loads(text)


def _sync_after_change(config: Config, name: str, message: str, sync) -> None:
    """管理表の変更後に git 同期（イベント駆動、R2-3）。

    sync 注入を優先（テスト/外部組み立て）、無ければ config から組み立てる
    （registry_sync_enabled 有効時のみ。無効なら no-op＝ローカルは git に触れない）。
    """
    service = sync if sync is not None else _build_sync(config)
    if service is None:
        return
    path = getattr(config, f"{name}_path")
    service.sync([path], message)


def _build_git(config: Config):
    """config から GitCliAdapter を組み立てる（registry_root を git リポとして操作）。"""
    from adapters.registry.git_cli import GitCliAdapter

    return GitCliAdapter(
        config.registry_root, remote=config.registry_remote, branch=config.registry_branch
    )


def _build_sync(config: Config):
    """config から RegistrySyncService を組み立てる（registry_sync_enabled 無効なら None）。"""
    if not config.registry_sync_enabled:
        return None
    from usecases.registry_sync import RegistrySyncService

    return RegistrySyncService(_build_git(config))


def run_registry_fetch(config: Config, git=None) -> int:
    """起動時に固定ブランチから管理表を fetch（R2-3、ROUTINE_PROMPT が起動時に呼ぶ）。

    registry_sync 無効なら no-op（exit 0＝ローカル運用は git に触れない）。git 注入は
    テスト用、本番は config から GitCliAdapter を組み立てる。fetch 失敗は
    EXIT_FETCH_FAILED（transient、次回起動で再試行）。
    """
    if not config.registry_sync_enabled:
        return EXIT_OK  # no-op
    service = git if git is not None else _build_git(config)
    try:
        service.fetch_checkout(config.registry_branch)
    except GitSyncError as exc:
        # 層3 可観測性: transient を沈黙して握り潰すと「気づけない空表稼働」になる。
        # 失敗の事実に加え、空表で継続＝記憶なし稼働という運用上の含意を警告で明示する
        # （principal への一報は ROUTINE_PROMPT 手順に委譲＝送信責務をコードに持たせない）。
        print(f"registry fetch failed: {exc}", file=sys.stderr)
        print(
            "WARNING: registry-sync is continuing with EMPTY tables — the secretary "
            "runs WITHOUT memory this session (individuals/tasks/knowledge/abilities, "
            "and any grants, are unavailable until the next successful fetch). "
            "Treat registry reads as empty and notify the principal that memory is unloaded.",
            file=sys.stderr,
        )
        return EXIT_FETCH_FAILED
    print(f"registry fetched: {config.registry_branch}")
    return EXIT_OK
