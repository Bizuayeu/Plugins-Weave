# tests/domain/test_message_id.py
"""
Message-ID 採番のテスト

new_message_id() のテスト。
"""

import os
import re
import sys

# scriptsディレクトリをパスに追加
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from domain.message_id import new_message_id


class TestNewMessageId:
    """new_message_id のテスト"""

    def test_returns_angle_bracketed_form(self):
        """<...@...> 形式（角括弧込み）を返す"""
        message_id = new_message_id()
        assert re.fullmatch(r"<[^<>@\s]+@[^<>@\s]+>", message_id)

    def test_no_duplicates_in_100_calls(self):
        """100回呼んで重複ゼロ"""
        ids = [new_message_id() for _ in range(100)]
        assert len(set(ids)) == 100
