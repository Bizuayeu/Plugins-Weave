#!/usr/bin/env python3
"""
Digest Setup CLI
================

初期セットアップCLI。Claudeから呼び出され、設定ファイル・ディレクトリ・初期ファイルを作成する。

Usage:
    python -m interfaces.digest_setup check
    python -m interfaces.digest_setup init --config '{"base_dir": "~/.claude/plugins/.episodicrag", ...}'
    python -m interfaces.digest_setup init --config '...' --force
"""

import argparse
import json
import shutil
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain.constants import LEVEL_CONFIG
from domain.file_constants import (
    CONFIG_FILENAME,
    DIGEST_TIMES_FILENAME,
    DIGEST_TIMES_TEMPLATE,
    GRAND_DIGEST_FILENAME,
    GRAND_DIGEST_TEMPLATE,
    PLUGIN_CONFIG_DIR,
    SHADOW_GRAND_DIGEST_FILENAME,
    SHADOW_GRAND_DIGEST_TEMPLATE,
)
from infrastructure.config import get_persistent_config_dir
from infrastructure.config.persistent_path import get_template_dir
from infrastructure.json_repository import save_json, try_load_json
from interfaces.cli_helpers import output_error, output_json

# デフォルトのbase_dir（永続化ディレクトリ）
DEFAULT_BASE_DIR = "~/.claude/plugins/.episodicrag"


@dataclass
class SetupResult:
    """セットアップ結果"""

    status: str  # "ok" | "error" | "already_configured"
    created: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)
    external_paths_detected: List[str] = field(default_factory=list)
    error: Optional[str] = None


class SetupManager:
    """セットアップマネージャー"""

    # 8階層のディレクトリ構成（LEVEL_CONFIGからSSoTとして生成）
    LEVEL_DIRS = [cfg["dir"] for cfg in LEVEL_CONFIG.values()]

    def __init__(self) -> None:
        """Initialize SetupManager"""
        self.persistent_config_dir = get_persistent_config_dir()
        self.config_file = self.persistent_config_dir / CONFIG_FILENAME
        self.template_dir = get_template_dir()

    def check(self) -> Dict[str, Any]:
        """
        セットアップ状態を確認

        Returns:
            状態を示すDict
        """
        config_exists = self.config_file.exists()

        # 設定ファイルが存在する場合、ディレクトリもチェック
        directories_exist = False
        if config_exists:
            config_data = try_load_json(self.config_file, log_on_error=False)
            if config_data is not None:
                try:
                    base_dir = self._resolve_base_dir(config_data.get("base_dir", DEFAULT_BASE_DIR))
                    paths = config_data.get("paths", {})
                    loops_dir = base_dir / paths.get("loops_dir", "data/Loops")
                    directories_exist = loops_dir.exists()
                except KeyError:
                    pass

        if config_exists and directories_exist:
            return {
                "status": "configured",
                "config_exists": True,
                "directories_exist": True,
                "config_file": str(self.config_file),
                "message": "Setup already completed",
            }
        elif config_exists:
            return {
                "status": "partial",
                "config_exists": True,
                "directories_exist": False,
                "config_file": str(self.config_file),
                "message": "Config exists but directories are missing",
            }
        else:
            return {
                "status": "not_configured",
                "config_exists": False,
                "directories_exist": False,
                "message": "Initial setup required",
            }

    def init(self, config_data: Dict[str, Any], force: bool = False) -> SetupResult:
        """
        セットアップ実行

        Args:
            config_data: 設定データ
            force: 既存設定を上書きするかどうか

        Returns:
            SetupResult
        """
        # 既存設定チェック
        if self.config_file.exists() and not force:
            return SetupResult(
                status="already_configured",
                error="Config file already exists. Use --force to overwrite.",
            )

        try:
            # 設定データのバリデーション
            validation_errors = self._validate_config_data(config_data)
            if validation_errors:
                return SetupResult(
                    status="error", error=f"Invalid config: {', '.join(validation_errors)}"
                )

            created: Dict[str, Any] = {"config_file": None, "directories": [], "files": []}
            warnings: List[str] = []

            # 1. 設定ファイル作成
            config_file_path = self._create_config_file(config_data)
            created["config_file"] = str(config_file_path)

            # 2. ディレクトリ作成
            created_dirs = self._create_directories(config_data)
            created["directories"] = created_dirs

            # 3. 初期ファイル作成
            created_files = self._create_initial_files(config_data)
            created["files"] = created_files

            # 4. 外部パス検出
            external_paths = self._detect_external_paths(config_data)

            return SetupResult(
                status="ok",
                created=created,
                warnings=warnings,
                external_paths_detected=external_paths,
            )

        except Exception as e:
            return SetupResult(status="error", error=str(e))

    def _validate_config_data(self, config_data: Dict[str, Any]) -> List[str]:
        """設定データのバリデーション"""
        errors = []

        # 必須フィールドチェック
        if "paths" not in config_data:
            errors.append("'paths' is required")
        else:
            paths = config_data["paths"]
            for key in ["loops_dir", "digests_dir", "essences_dir"]:
                if key not in paths:
                    errors.append(f"'paths.{key}' is required")

        if "levels" not in config_data:
            errors.append("'levels' is required")
        else:
            levels = config_data["levels"]
            for key in [
                "weekly_threshold",
                "monthly_threshold",
                "quarterly_threshold",
                "annual_threshold",
                "triennial_threshold",
                "decadal_threshold",
                "multi_decadal_threshold",
                "centurial_threshold",
            ]:
                if key not in levels:
                    errors.append(f"'levels.{key}' is required")
                elif not isinstance(levels[key], int) or levels[key] < 1:
                    errors.append(f"'levels.{key}' must be a positive integer")

        return errors

    def _resolve_base_dir(self, base_dir_str: str) -> Path:
        """base_dirを解決（絶対パス必須）"""
        base_path = Path(base_dir_str).expanduser()
        if not base_path.is_absolute():
            raise ValueError(f"base_dir must be an absolute path: {base_dir_str}")
        return base_path.resolve()

    def _create_config_file(self, config_data: Dict[str, Any]) -> Path:
        """設定ファイル作成"""
        # 永続化ディレクトリは get_persistent_config_dir() で自動作成される

        # コメント付きで保存
        full_config = {
            "_comment_base_dir": "データの基準ディレクトリ（絶対パス必須）",
            "base_dir": config_data.get("base_dir", DEFAULT_BASE_DIR),
            "_comment_trusted_external_paths": "外部パスへのアクセス許可リスト",
            "trusted_external_paths": config_data.get("trusted_external_paths", [DEFAULT_BASE_DIR]),
            "_comment_paths": "base_dirからの相対パスでデータ配置先を指定",
            "paths": config_data.get("paths", {}),
            "_comment_levels": "各階層のダイジェスト生成に必要なファイル数（Threshold）",
            "levels": config_data.get("levels", {}),
        }

        save_json(self.config_file, full_config)

        return self.config_file

    def _create_directories(self, config_data: Dict[str, Any]) -> List[str]:
        """ディレクトリ作成"""
        created_dirs = []

        base_dir = self._resolve_base_dir(config_data.get("base_dir", DEFAULT_BASE_DIR))
        paths = config_data.get("paths", {})

        # Loopsディレクトリ
        loops_dir = base_dir / paths.get("loops_dir", "data/Loops")
        loops_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(loops_dir))

        # Digestsディレクトリ（8階層 + Provisional）
        digests_dir = base_dir / paths.get("digests_dir", "data/Digests")
        for level_dir in self.LEVEL_DIRS:
            level_path = digests_dir / level_dir
            level_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(level_path))

            # Provisionalサブディレクトリ
            provisional_path = level_path / "Provisional"
            provisional_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(provisional_path))

        # Essencesディレクトリ
        essences_dir = base_dir / paths.get("essences_dir", "data/Essences")
        essences_dir.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(essences_dir))

        return created_dirs

    def _create_initial_files(self, config_data: Dict[str, Any]) -> List[str]:
        """初期ファイル作成（テンプレートから）"""
        created_files = []

        # テンプレートディレクトリがない場合はスキップ
        if self.template_dir is None:
            return created_files

        base_dir = self._resolve_base_dir(config_data.get("base_dir", DEFAULT_BASE_DIR))
        paths = config_data.get("paths", {})
        essences_dir = base_dir / paths.get("essences_dir", "data/Essences")

        # テンプレートファイルのコピー
        template_files = [
            (GRAND_DIGEST_TEMPLATE, essences_dir / GRAND_DIGEST_FILENAME),
            (SHADOW_GRAND_DIGEST_TEMPLATE, essences_dir / SHADOW_GRAND_DIGEST_FILENAME),
            (DIGEST_TIMES_TEMPLATE, self.persistent_config_dir / DIGEST_TIMES_FILENAME),
        ]

        for template_name, dest_path in template_files:
            template_path = self.template_dir / template_name
            if template_path.exists():
                shutil.copy(template_path, dest_path)
                created_files.append(dest_path.name)

        return created_files

    def _detect_external_paths(self, config_data: Dict[str, Any]) -> List[str]:
        """外部パス検出"""
        external_paths = []

        # base_dirのチェック
        base_dir_str = config_data.get("base_dir", DEFAULT_BASE_DIR)
        if self._is_external_path(base_dir_str):
            external_paths.append(f"base_dir: {base_dir_str}")

        # identity_file_pathのチェック
        identity_path = config_data.get("paths", {}).get("identity_file_path")
        if identity_path and self._is_external_path(identity_path):
            external_paths.append(f"identity_file_path: {identity_path}")

        return external_paths

    def _is_external_path(self, path_str: Optional[str]) -> bool:
        """パスが永続化ディレクトリ外を指すか判定"""
        if path_str is None:
            return False

        path = Path(path_str).expanduser()

        # 絶対パスの場合は永続化ディレクトリ外かチェック
        if path.is_absolute():
            try:
                path.resolve().relative_to(self.persistent_config_dir.resolve())
                return False  # 永続化ディレクトリ内
            except ValueError:
                return True  # 永続化ディレクトリ外

        # 相対パスは常に外部とみなす（base_dirは絶対パス必須のため）
        return True


def main() -> None:
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="EpisodicRAG Initial Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # check サブコマンド
    subparsers.add_parser("check", help="Check setup status")

    # init サブコマンド
    init_parser = subparsers.add_parser("init", help="Initialize setup")
    init_parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Configuration JSON string",
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite existing config",
    )

    args = parser.parse_args()

    try:
        manager = SetupManager()

        if args.command == "check":
            result = manager.check()
            output_json(result)

        elif args.command == "init":
            try:
                config_data = json.loads(args.config)
            except json.JSONDecodeError as e:
                output_error(f"Invalid JSON: {e}")
                return

            init_result = manager.init(config_data, force=args.force)
            output_json(asdict(init_result))

        else:
            parser.print_help()
            sys.exit(1)

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
