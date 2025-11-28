#!/usr/bin/env python3
"""
JSON Operations - 基本的なJSON操作
==================================

JSONファイルの読み書きに関する低レベル操作を提供。

## 設計意図

ARCHITECTURE: Single Responsibility Principle (SOLID-S)
JSON操作のプリミティブをこのモジュールに集約し、
他のモジュールは組み合わせ・抽象化に専念する。

## 関数の責務

| 関数 | 責務 |
|------|------|
| safe_read_json | JSONファイルを安全に読み込む（共通ヘルパー） |
| load_json | 必須ファイルの読み込み（エラーは例外） |
| save_json | ファイル保存（親ディレクトリ自動作成） |
| try_load_json | オプショナルファイル読み込み（エラーはdefault） |
| try_read_json_from_file | バッチ処理向け読み込み（拡張子チェック付き） |
| file_exists | ファイル存在チェック |
| ensure_directory | ディレクトリ保証 |
| confirm_file_overwrite | 上書き確認 |
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, cast

from domain.constants import DIGEST_FILE_EXTENSION
from domain.error_formatter import get_error_formatter
from domain.exceptions import FileIOError

# モジュールロガー
logger = logging.getLogger("episodic_rag")


def safe_read_json(file_path: Path, raise_on_error: bool = True) -> Optional[Dict[str, Any]]:
    """
    JSONファイルを安全に読み込む共通ヘルパー

    Args:
        file_path: 読み込むJSONファイルのパス
        raise_on_error: エラー時に例外を発生させるか（Falseの場合はNoneを返す）

    Returns:
        読み込んだdict、またはエラー時はNone（raise_on_error=Falseの場合）

    Raises:
        FileIOError: raise_on_error=Trueの場合、JSONパースまたはI/Oエラー時
    """
    formatter = get_error_formatter()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        if raise_on_error:
            raise FileIOError(formatter.file.invalid_json(file_path, e)) from e
        return None
    except IOError as e:
        if raise_on_error:
            raise FileIOError(formatter.file.file_io_error("read", file_path, e)) from e
        return None


def load_json(file_path: Path) -> Dict[str, Any]:
    """
    JSONファイルを読み込む

    必須ファイルの読み込みに使用。ファイルが存在しない場合は例外。

    Args:
        file_path: 読み込むJSONファイルのパス

    Returns:
        読み込んだdict

    Raises:
        FileIOError: ファイルが存在しない、またはJSONのパースに失敗した場合
    """
    if not file_path.exists():
        formatter = get_error_formatter()
        raise FileIOError(formatter.file.file_not_found(file_path))

    result = safe_read_json(file_path, raise_on_error=True)
    # safe_read_jsonがraise_on_error=Trueで呼ばれた場合、Noneは返らない
    return cast(Dict[str, Any], result)


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
    formatter = get_error_formatter()
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    except IOError as e:
        raise FileIOError(formatter.file.file_io_error("write", file_path, e)) from e


def try_load_json(
    file_path: Path, default: Optional[Dict[str, Any]] = None, log_on_error: bool = True
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
        data = try_load_json(path, default={})

        # ファイルがなければNoneを返す
        data = try_load_json(path)
        if data is None:
            # 初期化処理
    """
    if not file_path.exists():
        return default

    result = safe_read_json(file_path, raise_on_error=False)
    if result is None and log_on_error:
        logger.warning(f"Failed to load JSON from {file_path}")
    return result if result is not None else default


def try_read_json_from_file(file_path: Path, log_on_error: bool = True) -> Optional[Dict[str, Any]]:
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
            data = try_read_json_from_file(source_path / source_file)
            if data is None:
                skipped_count += 1
                continue
            # 処理を続行
    """
    if not file_path.exists():
        return None

    if file_path.suffix != DIGEST_FILE_EXTENSION:
        return None

    result = safe_read_json(file_path, raise_on_error=False)
    if result is None and log_on_error:
        logger.warning(f"Failed to parse {file_path.name} as JSON (skipped)")
    return result


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
    formatter = get_error_formatter()
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise FileIOError(formatter.file.directory_creation_failed(dir_path, e)) from e


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


__all__ = [
    "safe_read_json",
    "load_json",
    "save_json",
    "try_load_json",
    "try_read_json_from_file",
    "file_exists",
    "ensure_directory",
    "confirm_file_overwrite",
]
