#!/usr/bin/env python3
"""
Utility Functions
=================

共通ユーティリティ関数を提供するモジュール。
finalize_from_shadow.py から分離。
"""
import json
import logging
import re
import sys
from pathlib import Path
from typing import Optional, Callable, Dict, Any


# =============================================================================
# ロギング設定
# =============================================================================

# モジュールロガー
logger = logging.getLogger("episodic_rag")

# デフォルトハンドラー設定（未設定の場合のみ）
if not logger.handlers:
    # stderrハンドラー（WARNING以上）
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    # stdoutハンドラー（INFO）
    class StdoutFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.levelno == logging.INFO

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(StdoutFilter())
    stdout_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))

    logger.addHandler(stderr_handler)
    logger.addHandler(stdout_handler)
    logger.setLevel(logging.INFO)


# =============================================================================
# ロギング関数（後方互換ラッパー）
# =============================================================================

def log_error(message: str, exit_code: Optional[int] = None) -> None:
    """
    エラーメッセージを出力

    Args:
        message: エラーメッセージ
        exit_code: 指定時はこのコードでプログラムを終了
    """
    logger.error(message)
    if exit_code is not None:
        sys.exit(exit_code)


def log_warning(message: str) -> None:
    """
    警告メッセージを出力

    Args:
        message: 警告メッセージ
    """
    logger.warning(message)


def log_info(message: str) -> None:
    """
    情報メッセージを出力

    Args:
        message: 情報メッセージ
    """
    logger.info(message)


# =============================================================================
# ファイル名処理
# =============================================================================


def sanitize_filename(title: str, max_length: int = 50) -> str:
    """
    ファイル名として安全な文字列に変換

    Args:
        title: 元のタイトル文字列
        max_length: 最大文字数（デフォルト: 50）

    Returns:
        ファイル名として安全な文字列（空の場合は"untitled"）

    Raises:
        TypeError: titleがstr型でない場合
        ValueError: max_lengthが正の整数でない場合
    """
    # 型チェック
    if not isinstance(title, str):
        raise TypeError(f"title must be str, got {type(title).__name__}")
    if max_length <= 0:
        raise ValueError(f"max_length must be positive, got {max_length}")

    # 危険な文字を削除
    sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
    # 空白をアンダースコアに変換
    sanitized = re.sub(r'\s+', '_', sanitized)
    # 先頭・末尾のアンダースコアを削除
    sanitized = sanitized.strip('_')
    # 長さ制限
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip('_')

    # 結果が空の場合
    if not sanitized:
        return "untitled"

    return sanitized


# =============================================================================
# JSON ファイル操作
# =============================================================================


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
        json.JSONDecodeError: JSONのパースに失敗した場合
        IOError: ファイルの読み込みに失敗した場合
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
            log_info(msg)
            return template

        # デフォルトファクトリーがある場合はそれを使用
        if default_factory:
            template = default_factory()
            if save_on_create:
                save_json(target_file, template)
            msg = log_message or f"Created {target_file.name} with default template"
            log_info(msg)
            return template

        # どちらもない場合は空のdictを返す
        return {}

    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON in {target_file}: {e}")
        raise
    except IOError as e:
        log_error(f"Failed to read {target_file}: {e}")
        raise


def save_json(file_path: Path, data: Dict[str, Any], indent: int = 2) -> None:
    """
    dictをJSONファイルに保存（親ディレクトリ自動作成）。

    Args:
        file_path: 保存先のパス
        data: 保存するdict
        indent: インデント幅（デフォルト: 2）

    Raises:
        IOError: ファイルの書き込みに失敗した場合
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
    except IOError as e:
        log_error(f"Failed to write {file_path}: {e}")
        raise


# =============================================================================
# Digest番号操作
# =============================================================================


def get_next_digest_number(digests_path: Path, level: str) -> int:
    """
    指定レベルの次のDigest番号を取得。

    既存のRegularDigestファイルをスキャンし、最大番号+1を返す。
    ファイルが存在しない場合は1を返す。

    Args:
        digests_path: Digestsディレクトリのパス
        level: Digestレベル（weekly, monthly, quarterly, annual,
               triennial, decadal, multi_decadal, centurial）

    Returns:
        次の番号（1始まり）

    Raises:
        ValueError: 無効なlevelが指定された場合
    """
    # 循環インポートを避けるためローカルインポート
    from config import LEVEL_CONFIG, extract_file_number

    config = LEVEL_CONFIG.get(level)
    if not config:
        raise ValueError(f"Invalid level: {level}")

    prefix = config["prefix"]
    level_dir = digests_path / config["dir"]

    if not level_dir.exists():
        return 1

    # 既存ファイルから最大番号を取得
    max_num = 0
    pattern = f"{prefix}*_*.txt"

    for f in level_dir.glob(pattern):
        result = extract_file_number(f.name)
        if result and result[0] == prefix:
            max_num = max(max_num, result[1])

    return max_num + 1
