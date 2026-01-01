# adapters/cli/decorators.py
"""
CLIハンドラ用デコレータ

Stage 2: バリデーション重複解消
"""

from __future__ import annotations

from argparse import Namespace
from collections.abc import Callable
from functools import wraps

from domain.config import Config

# ハンドラ型: argsを受け取り、終了コードを返す
Handler = Callable[[Namespace], int]


def validate_config(handler: Handler) -> Handler:
    """
    設定バリデーションを行うデコレータ。

    Config.load()で設定を読み込み、validate()でバリデーションを行う。
    エラーがある場合はエラーメッセージを出力して1を返す。
    エラーがない場合は元のハンドラを実行する。

    Args:
        handler: ラップするハンドラ関数

    Returns:
        バリデーション付きハンドラ

    Stage 2: バリデーション重複解消
    """

    @wraps(handler)
    def wrapper(args: Namespace) -> int:
        config = Config.load()
        errors = config.validate()
        if errors:
            for err in errors:
                print(f"Error: {err}")
            return 1
        return handler(args)

    return wrapper


__all__ = ["validate_config"]
