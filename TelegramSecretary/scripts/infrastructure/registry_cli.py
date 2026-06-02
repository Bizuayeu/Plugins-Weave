"""管理表（INDIVIDUALS / TASKS / KNOWLEDGE）CRUD の CLI ハンドラ。

main.py の subcommand から呼ばれる。値オブジェクトで入力を検証してから永続化する
（決定論的 I/O。何を登録/更新するかの判断は エージェント = 重要度の世界）。
"""
from __future__ import annotations

import json
import sys
from typing import Any

from adapters.registry.json_registry_store import JsonRegistryStore
from domain.registry import Individual, Knowledge, Task
from infrastructure.config import Config
from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_OK
from usecases.manage_registry import RegistryService

# name -> (Config の path property 名, キーフィールド, 値オブジェクトクラス)
_REGISTRY_SPEC = {
    "individuals": ("individuals_path", "uuid", Individual),
    "tasks": ("tasks_path", "id", Task),
    "knowledge": ("knowledge_path", "id", Knowledge),
}


def _service(config: Config, name: str) -> RegistryService:
    path_attr, key_field, _ = _REGISTRY_SPEC[name]
    return RegistryService(JsonRegistryStore(getattr(config, path_attr)), key_field)


def run_registry_command(config: Config, name: str, action: str, args: Any) -> int:
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
        print(f"saved {name} {key_field}={record[key_field]}")
        return EXIT_OK

    if action == "remove":
        svc.remove(args.key)
        print(f"removed {name} {key_field}={args.key}")
        return EXIT_OK

    print(f"unknown action: {action}", file=sys.stderr)
    return EXIT_CONFIG_INVALID


def _read_json_arg(args: Any) -> dict:
    """--json または --json-file から1レコードの dict を読む。"""
    if getattr(args, "json_file", None):
        text = open(args.json_file, encoding="utf-8").read()
    else:
        text = args.json
    return json.loads(text)
