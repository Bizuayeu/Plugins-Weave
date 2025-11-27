#!/usr/bin/env python3
"""
JSON Repository
===============

JSONファイルの読み書きを担当するインフラストラクチャ層。
ファイルI/O操作を抽象化し、エラーハンドリングを一元管理。

Usage:
    from infrastructure.json_repository import load_json, save_json, load_json_with_template
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from domain.exceptions import FileIOError

# モジュールロガー
logger = logging.getLogger("episodic_rag")


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    JSONファイルを読み込む

    Args:
        file_path: 読み込むJSONファイルのパス

    Returns:
        読み込んだdict

    Raises:
        FileIOError: ファイルが存在しない、またはJSONのパースに失敗した場合
    """
    if not file_path.exists():
        raise FileIOError(f"File not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise FileIOError(f"Invalid JSON in {file_path}: {e}")
    except IOError as e:
        raise FileIOError(f"Failed to read {file_path}: {e}")


def save_json(file_path: Path, data: Dict[str, Any], indent: int = 2) -> None:
    """
    dictをJSONファイルに保存（親ディレクトリ自動作成）

    Args:
        file_path: 保存先のパス
        data: 保存するdict
        indent: インデント幅（デフォルト: 2）

    Raises:
        FileIOError: ファイルの書き込みに失敗した場合
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    except IOError as e:
        raise FileIOError(f"Failed to write {file_path}: {e}")


def load_json_with_template(
    target_file: Path,
    template_file: Optional[Path] = None,
    default_factory: Optional[Callable[[], Dict[str, Any]]] = None,
    save_on_create: bool = True,
    log_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    JSONファイルを読み込む。存在しない場合はテンプレートまたはデフォルトから作成。

    Args:
        target_file: 読み込むJSONファイルのパス
        template_file: テンプレートファイルのパス（オプション）
        default_factory: テンプレートがない場合のデフォルト生成関数
        save_on_create: 作成時に保存するかどうか
        log_message: 作成時のログメッセージ（Noneの場合はデフォルトメッセージ）

    Returns:
        読み込んだまたは作成したdict

    Raises:
        FileIOError: JSONのパース失敗またはファイルI/Oエラーの場合
    """
    try:
        # ファイルが存在する場合はそのまま読み込み
        if target_file.exists():
            with open(target_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # テンプレートファイルが存在する場合はそこから初期化
        if template_file and template_file.exists():
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
            if save_on_create:
                save_json(target_file, template)
            msg = log_message or f"Initialized {target_file.name} from template"
            logger.info(msg)
            return template

        # デフォルトファクトリーがある場合はそれを使用
        if default_factory:
            template = default_factory()
            if save_on_create:
                save_json(target_file, template)
            msg = log_message or f"Created {target_file.name} with default template"
            logger.info(msg)
            return template

        # どちらもない場合は空のdictを返す
        return {}

    except json.JSONDecodeError as e:
        raise FileIOError(f"Invalid JSON in {target_file}: {e}")
    except IOError as e:
        raise FileIOError(f"Failed to read {target_file}: {e}")


def file_exists(file_path: Path) -> bool:
    """
    ファイルが存在するかチェック

    Args:
        file_path: チェックするファイルのパス

    Returns:
        存在すればTrue
    """
    return file_path.exists()


def ensure_directory(dir_path: Path) -> None:
    """
    ディレクトリが存在することを保証する（なければ作成）

    Args:
        dir_path: 作成するディレクトリのパス

    Raises:
        FileIOError: ディレクトリの作成に失敗した場合
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise FileIOError(f"Failed to create directory {dir_path}: {e}")
