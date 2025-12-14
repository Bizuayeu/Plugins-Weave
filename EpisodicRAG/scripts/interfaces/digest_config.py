#!/usr/bin/env python3
"""
Digest Config CLI
=================

設定変更CLI。Claudeから呼び出され、設定ファイルを読み取り・変更する。

Usage:
    python -m interfaces.digest_config show
    python -m interfaces.digest_config update --config '{"base_dir": ".", ...}'
    python -m interfaces.digest_config set --key "levels.weekly_threshold" --value 7
    python -m interfaces.digest_config trusted-paths add "~/DEV/production"
    python -m interfaces.digest_config trusted-paths remove "~/DEV/production"
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from domain.exceptions import FileIOError
from domain.file_constants import CONFIG_FILENAME
from infrastructure.config import get_persistent_config_dir
from infrastructure.json_repository import load_json, save_json
from interfaces.cli_helpers import output_error, output_json


class ConfigEditor:
    """設定エディタ"""

    def __init__(self, plugin_root: Optional[Path] = None):
        """
        Args:
            plugin_root: Pluginルート（指定しない場合は自動検出を試みる）
        """
        if plugin_root:
            self.plugin_root = Path(plugin_root).resolve()
        else:
            # スクリプトの場所から推測
            self.plugin_root = Path(__file__).resolve().parent.parent.parent

        self.config_file = get_persistent_config_dir() / CONFIG_FILENAME

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        return load_json(self.config_file)

    def _save_config(self, config_data: Dict[str, Any]) -> None:
        """設定ファイルを保存する"""
        save_json(self.config_file, config_data)

    def _resolve_path(self, path_str: str) -> Path:
        """パスを解決して絶対パスを返す"""
        path = Path(path_str).expanduser()
        if not path.is_absolute():
            # base_dirを考慮して解決
            config = self._load_config()
            base_dir = Path(config.get("base_dir", ".")).expanduser()
            if not base_dir.is_absolute():
                base_dir = self.plugin_root / base_dir
            path = base_dir / path
        return path.resolve()

    def show(self) -> Dict[str, Any]:
        """
        現在の設定を取得

        Returns:
            設定データと解決後のパス
        """
        config_data = self._load_config()

        # コメントフィールドを除去
        clean_config = {k: v for k, v in config_data.items() if not k.startswith("_comment")}

        # 解決後のパスを計算
        base_dir_str = config_data.get("base_dir", ".")
        base_dir = Path(base_dir_str).expanduser()
        if not base_dir.is_absolute():
            base_dir = self.plugin_root / base_dir
        base_dir = base_dir.resolve()

        paths = config_data.get("paths", {})
        resolved_paths = {
            "plugin_root": str(self.plugin_root),
            "base_dir": str(base_dir),
            "loops_path": str(base_dir / paths.get("loops_dir", "data/Loops")),
            "digests_path": str(base_dir / paths.get("digests_dir", "data/Digests")),
            "essences_path": str(base_dir / paths.get("essences_dir", "data/Essences")),
        }

        if paths.get("identity_file_path"):
            identity_path = Path(paths["identity_file_path"]).expanduser()
            if not identity_path.is_absolute():
                identity_path = base_dir / identity_path
            resolved_paths["identity_file_path"] = str(identity_path.resolve())

        return {
            "status": "ok",
            "config": clean_config,
            "resolved_paths": resolved_paths,
        }

    def update(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        設定を完全更新

        Args:
            new_config: 新しい設定データ

        Returns:
            更新結果
        """
        # 既存設定を読み込み
        current_config = self._load_config()

        # コメントを保持しつつ更新
        updated_config = {}
        for key in current_config:
            if key.startswith("_comment"):
                updated_config[key] = current_config[key]
            elif key in new_config:
                updated_config[key] = new_config[key]
            else:
                updated_config[key] = current_config[key]

        # 新しいキーがあれば追加
        for key in new_config:
            if key not in updated_config and not key.startswith("_comment"):
                updated_config[key] = new_config[key]

        self._save_config(updated_config)

        return {
            "status": "ok",
            "message": "Config updated successfully",
            "updated_keys": list(new_config.keys()),
        }

    def set_value(self, key: str, value: Any) -> Dict[str, Any]:
        """
        個別設定を更新（ドット記法サポート）

        Args:
            key: 設定キー（例: "levels.weekly_threshold", "paths.loops_dir"）
            value: 新しい値

        Returns:
            更新結果
        """
        config_data = self._load_config()

        # ドット記法でネストされたキーをパース
        keys = key.split(".")
        current = config_data
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # 値の型変換（threshold は整数）
        final_key = keys[-1]
        if "threshold" in final_key and isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                return {
                    "status": "error",
                    "error": f"Value for {key} must be an integer",
                }

        old_value = current.get(final_key)
        current[final_key] = value

        self._save_config(config_data)

        return {
            "status": "ok",
            "message": f"Updated {key}",
            "old_value": old_value,
            "new_value": value,
        }

    def add_trusted_path(self, path: str) -> Dict[str, Any]:
        """
        trusted_external_paths にパスを追加

        Args:
            path: 追加するパス（絶対パスまたは~で始まるパス）

        Returns:
            更新結果
        """
        # パスの検証
        expanded = Path(path).expanduser()
        if not expanded.is_absolute() and not path.startswith("~"):
            return {
                "status": "error",
                "error": "Path must be absolute or start with ~",
            }

        config_data = self._load_config()

        if "trusted_external_paths" not in config_data:
            config_data["trusted_external_paths"] = []

        trusted_paths: List[str] = config_data["trusted_external_paths"]

        if path in trusted_paths:
            return {
                "status": "ok",
                "message": f"Path already exists: {path}",
                "trusted_external_paths": trusted_paths,
            }

        trusted_paths.append(path)
        self._save_config(config_data)

        return {
            "status": "ok",
            "message": f"Added path: {path}",
            "trusted_external_paths": trusted_paths,
        }

    def remove_trusted_path(self, path: str) -> Dict[str, Any]:
        """
        trusted_external_paths からパスを削除

        Args:
            path: 削除するパス

        Returns:
            更新結果
        """
        config_data = self._load_config()
        trusted_paths: List[str] = config_data.get("trusted_external_paths", [])

        if path not in trusted_paths:
            return {
                "status": "error",
                "error": f"Path not found: {path}",
                "trusted_external_paths": trusted_paths,
            }

        trusted_paths.remove(path)
        self._save_config(config_data)

        return {
            "status": "ok",
            "message": f"Removed path: {path}",
            "trusted_external_paths": trusted_paths,
        }

    def list_trusted_paths(self) -> Dict[str, Any]:
        """
        trusted_external_paths を一覧表示

        Returns:
            パス一覧
        """
        config_data = self._load_config()
        trusted_paths = config_data.get("trusted_external_paths", [])

        return {
            "status": "ok",
            "trusted_external_paths": trusted_paths,
            "count": len(trusted_paths),
        }


def main(plugin_root: Optional[Path] = None) -> None:
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="EpisodicRAG Configuration Editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # show サブコマンド
    subparsers.add_parser("show", help="Show current configuration")

    # update サブコマンド
    update_parser = subparsers.add_parser("update", help="Update entire configuration")
    update_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Configuration JSON string",
    )

    # set サブコマンド
    set_parser = subparsers.add_parser("set", help="Set a single configuration value")
    set_parser.add_argument(
        "--key",
        type=str,
        required=True,
        help="Configuration key (dot notation: levels.weekly_threshold)",
    )
    set_parser.add_argument(
        "--value",
        type=str,
        required=True,
        help="New value",
    )

    # trusted-paths サブコマンド
    trusted_parser = subparsers.add_parser("trusted-paths", help="Manage trusted external paths")
    trusted_subparsers = trusted_parser.add_subparsers(dest="trusted_command")

    _trusted_list = trusted_subparsers.add_parser("list", help="List trusted paths")  # noqa: F841

    trusted_add = trusted_subparsers.add_parser("add", help="Add a trusted path")
    trusted_add.add_argument("path", type=str, help="Path to add")

    trusted_remove = trusted_subparsers.add_parser("remove", help="Remove a trusted path")
    trusted_remove.add_argument("path", type=str, help="Path to remove")

    # --plugin-root オプション（全コマンド共通）
    parser.add_argument(
        "--plugin-root",
        type=Path,
        help="Override plugin root (for testing)",
    )

    args = parser.parse_args()

    # plugin_rootの決定
    effective_root = args.plugin_root if args.plugin_root else plugin_root

    try:
        editor = ConfigEditor(plugin_root=effective_root)

        if args.command == "show":
            result = editor.show()
            output_json(result)

        elif args.command == "update":
            try:
                config_data = json.loads(args.config)
            except json.JSONDecodeError as e:
                output_error(f"Invalid JSON: {e}")
                return

            result = editor.update(config_data)
            output_json(result)

        elif args.command == "set":
            # 値の型を推測
            raw_value: str = args.value
            value: Union[str, int, bool, None]
            lower_value = raw_value.lower()
            if lower_value == "true":
                value = True
            elif lower_value == "false":
                value = False
            elif lower_value == "null" or lower_value == "none":
                value = None
            elif raw_value.isdigit() or (raw_value.startswith("-") and raw_value[1:].isdigit()):
                value = int(raw_value)
            else:
                value = raw_value

            result = editor.set_value(args.key, value)
            output_json(result)

        elif args.command == "trusted-paths":
            if args.trusted_command == "list" or args.trusted_command is None:
                result = editor.list_trusted_paths()
                output_json(result)
            elif args.trusted_command == "add":
                result = editor.add_trusted_path(args.path)
                output_json(result)
            elif args.trusted_command == "remove":
                result = editor.remove_trusted_path(args.path)
                output_json(result)
            else:
                trusted_parser.print_help()
                sys.exit(1)

        else:
            parser.print_help()
            sys.exit(1)

    except FileIOError as e:
        output_error(str(e), {"action": "Run @digest-setup first"})
    except Exception as e:
        output_error(str(e))


if __name__ == "__main__":
    import io

    # Windows UTF-8入出力対応
    if sys.platform == "win32":
        sys.stdin = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8")
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    main()
