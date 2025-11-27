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
        raise FileIOError(f"Invalid JSON in {file_path}: {e}") from e
    except IOError as e:
        raise FileIOError(f"Failed to read {file_path}: {e}") from e


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
        raise FileIOError(f"Failed to write {file_path}: {e}") from e


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
    logger.debug(f"load_json_with_template called: target={target_file}, template={template_file}")

    try:
        # ファイルが存在する場合はそのまま読み込み
        if target_file.exists():
            logger.debug(f"Loading existing file: {target_file}")
            with open(target_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Loaded {len(data)} keys from {target_file.name}")
            return data

        # テンプレートファイルが存在する場合はそこから初期化
        if template_file and template_file.exists():
            logger.debug(f"Target not found, loading from template: {template_file}")
            with open(template_file, 'r', encoding='utf-8') as f:
                template = json.load(f)
            if save_on_create:
                save_json(target_file, template)
                logger.debug(f"Saved initialized file to: {target_file}")
            msg = log_message or f"Initialized {target_file.name} from template"
            logger.info(msg)
            return template

        # デフォルトファクトリーがある場合はそれを使用
        if default_factory:
            logger.debug(f"No template found, using default_factory")
            template = default_factory()
            if save_on_create:
                save_json(target_file, template)
                logger.debug(f"Saved default template to: {target_file}")
            msg = log_message or f"Created {target_file.name} with default template"
            logger.info(msg)
            return template

        # どちらもない場合は空のdictを返す
        logger.debug(f"No template or factory provided, returning empty dict")
        return {}

    except json.JSONDecodeError as e:
        logger.debug(f"JSON decode error in {target_file}: {e}")
        raise FileIOError(f"Invalid JSON in {target_file}: {e}") from e
    except IOError as e:
        logger.debug(f"IO error reading {target_file}: {e}")
        raise FileIOError(f"Failed to read {target_file}: {e}") from e


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
        raise FileIOError(f"Failed to create directory {dir_path}: {e}") from e


def safe_load_json(
    file_path: Path,
    default: Optional[Dict[str, Any]] = None,
    log_on_error: bool = True
) -> Optional[Dict[str, Any]]:
    """
    JSONファイルを安全に読み込む（エラー時はデフォルト値を返す）

    エラーが発生しても例外を投げず、デフォルト値を返す。
    グレースフルデグラデーションが必要な場合に使用。

    Args:
        file_path: 読み込むJSONファイルのパス
        default: エラー時に返すデフォルト値（デフォルト: None）
        log_on_error: エラー時にログを出力するかどうか

    Returns:
        読み込んだdict、またはエラー時はdefault値

    Example:
        # ファイルがなければ空dictを返す
        data = safe_load_json(path, default={})

        # ファイルがなければNoneを返す
        data = safe_load_json(path)
        if data is None:
            # 初期化処理
    """
    if not file_path.exists():
        return default

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        if log_on_error:
            logger.warning(f"Failed to load JSON from {file_path}: {e}")
        return default


def confirm_file_overwrite(file_path: Path, force: bool = False) -> bool:
    """
    ファイルの上書き確認を行う

    既存ファイルがある場合の上書き可否を判定する。
    CLIツールでの対話的確認には使用せず、プログラム的な判定に使用。

    Args:
        file_path: 確認するファイルのパス
        force: 強制上書きフラグ（Trueなら常に上書き可）

    Returns:
        上書き可能ならTrue、不可ならFalse

    Example:
        if not confirm_file_overwrite(output_path):
            raise FileIOError(f"File already exists: {output_path}")
    """
    if not file_path.exists():
        return True
    return force


def read_json_from_file_safe(
    file_path: Path,
    log_on_error: bool = True
) -> Optional[Dict[str, Any]]:
    """
    JSONファイルを安全に読み込む（個別ファイル処理用）

    ループ内で複数ファイルを処理する際に使用。
    エラー時はスキップしてNoneを返す。

    Args:
        file_path: 読み込むファイルパス
        log_on_error: エラー時にログ出力するか

    Returns:
        読み込んだdict、またはエラー時はNone

    Example:
        for source_file in source_files:
            data = read_json_from_file_safe(source_path / source_file)
            if data is None:
                skipped_count += 1
                continue
            # 処理を続行
    """
    if not file_path.exists():
        return None

    if file_path.suffix != '.txt':
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        if log_on_error:
            logger.warning(f"Failed to parse {file_path.name} as JSON (skipped)")
        return None
    except OSError as e:
        if log_on_error:
            logger.warning(f"Error reading {file_path.name}: {e} (skipped)")
        return None
