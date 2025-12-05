#!/usr/bin/env python3
"""
User Interaction Utilities
===========================

ユーザー確認プロンプトを提供するインフラストラクチャ層ユーティリティ。

Usage:
    from infrastructure.user_interaction import get_default_confirm_callback

    callback = get_default_confirm_callback()
    if callback("ファイルを上書きしますか？"):
        # 処理続行
"""

from typing import Callable

__all__ = ["get_default_confirm_callback"]


def get_default_confirm_callback() -> Callable[[str], bool]:
    """
    デフォルトの確認コールバック関数を取得

    Returns:
        メッセージを受け取りboolを返すcallable

    Example:
        callback = get_default_confirm_callback()
        approved = callback("Continue?")
        approved  # True if user entered 'y', False otherwise
    """

    def _default_confirm(message: str) -> bool:
        """
        デフォルトの対話的確認コールバック

        Args:
            message: 確認メッセージ

        Returns:
            ユーザーが'y'と回答した場合True、非対話環境では自動承認
        """
        try:
            response = input(f"{message} (y/n): ")
            return response.lower() == "y"
        except EOFError:
            return True  # 非対話環境では自動承認

    return _default_confirm
