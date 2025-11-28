#!/usr/bin/env python3
"""
JSON Repository
===============

JSONファイルの読み書きを担当するインフラストラクチャ層。
ファイルI/O操作を抽象化し、エラーハンドリングを一元管理。

## パッケージ構成

```
json_repository/
├── __init__.py        # 公開API
├── operations.py      # 基本操作（load_json, save_json等）
├── load_strategy.py   # Strategy Pattern実装
└── chained_loader.py  # Chain of Responsibility
```

## JSON読み込み関数の使い分け

| 関数 | 用途 | エラー時の動作 |
|------|------|----------------|
| load_json() | 必須ファイルの読み込み | 例外をスロー |
| try_load_json() | オプショナルファイル | デフォルト値を返却 |
| try_read_json_from_file() | バッチ処理向け | None/デフォルト返却 |
| load_json_with_template() | テンプレート付き | 3段階フォールバック |

## 設計パターン

ARCHITECTURE: Strategy Pattern
load_json_with_templateの読み込みロジックを戦略クラスに分離。
- FileLoadStrategy: 既存ファイル読み込み
- TemplateLoadStrategy: テンプレートから初期化
- FactoryLoadStrategy: ファクトリから生成
- DefaultLoadStrategy: 空dictフォールバック

ARCHITECTURE: Chain of Responsibility
ChainedLoaderが戦略を順番に試行し、最初に成功したものを返す。

Usage:
    from infrastructure.json_repository import load_json, save_json, load_json_with_template
    from infrastructure.json_repository import try_load_json, try_read_json_from_file
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, TypeVar

from infrastructure.json_repository.chained_loader import ChainedLoader
from infrastructure.json_repository.load_strategy import (
    DefaultLoadStrategy,
    FactoryLoadStrategy,
    FileLoadStrategy,
    LoadContext,
    LoadStrategy,
    TemplateLoadStrategy,
)
from infrastructure.json_repository.operations import (
    confirm_file_overwrite,
    ensure_directory,
    file_exists,
    load_json,
    safe_read_json,
    save_json,
    try_load_json,
    try_read_json_from_file,
)

# モジュールロガー
logger = logging.getLogger("episodic_rag")

# Generic type for load_json_with_template
T = TypeVar("T", bound=Mapping[str, Any])


def load_json_with_template(
    target_file: Path,
    template_file: Optional[Path] = None,
    default_factory: Optional[Callable[[], T]] = None,
    save_on_create: bool = True,
    log_message: Optional[str] = None,
) -> T:
    """
    JSONファイルを読み込む。存在しない場合はテンプレートまたはデフォルトから作成。

    ARCHITECTURE: Strategy Pattern + Chain of Responsibility
    内部で4つの戦略を順番に試行:
    1. FileLoadStrategy: 既存ファイルから読み込み
    2. TemplateLoadStrategy: テンプレートから初期化
    3. FactoryLoadStrategy: ファクトリから生成
    4. DefaultLoadStrategy: 空dictを返す

    Generic type T allows callers to avoid explicit casts when using TypedDict.

    Args:
        target_file: 読み込むJSONファイルのパス
        template_file: テンプレートファイルのパス（オプション）
        default_factory: テンプレートがない場合のデフォルト生成関数
        save_on_create: 作成時に保存するかどうか
        log_message: 作成時のログメッセージ（Noneの場合はデフォルトメッセージ）

    Returns:
        読み込んだまたは作成したdict (type T)

    Raises:
        FileIOError: JSONのパース失敗またはファイルI/Oエラーの場合

    Example:
        # With TypedDict, the factory type determines the return type:
        def get_template() -> MyTypedDict:
            return {"key": "value"}

        data = load_json_with_template(path, default_factory=get_template)
        # data is inferred as MyTypedDict
    """
    logger.debug(
        f"load_json_with_template called: target={target_file}, template={template_file}"
    )

    # コンテキスト作成
    context = LoadContext(
        target_file=target_file,
        template_file=template_file,
        default_factory=default_factory,
        save_on_create=save_on_create,
        log_message=log_message,
    )

    # 戦略チェーン構築
    # ARCHITECTURE: Chain of Responsibility
    # 各戦略を順番に試行し、最初に成功したものを返す
    loader: ChainedLoader[T] = ChainedLoader([
        FileLoadStrategy(safe_read_json),
        TemplateLoadStrategy(safe_read_json, save_json),
        FactoryLoadStrategy(save_json),
        DefaultLoadStrategy(),
    ])

    result = loader.load(context)
    # DefaultLoadStrategyが最後にあるため、Noneは返らない
    assert result is not None, "ChainedLoader should never return None with DefaultLoadStrategy"
    return result


# 公開API
__all__ = [
    # 基本操作
    "load_json",
    "save_json",
    "load_json_with_template",
    "file_exists",
    "ensure_directory",
    "try_load_json",
    "confirm_file_overwrite",
    "try_read_json_from_file",
    # 低レベルAPI（上級者向け）
    "safe_read_json",
    # Strategy Pattern（拡張用）
    "LoadStrategy",
    "LoadContext",
    "FileLoadStrategy",
    "TemplateLoadStrategy",
    "FactoryLoadStrategy",
    "DefaultLoadStrategy",
    # Chain of Responsibility（拡張用）
    "ChainedLoader",
]
