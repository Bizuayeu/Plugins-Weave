# domain/message_id.py
"""
Message-ID 採番

Entities層: 送信メールの一意識別子を発行する。台帳の主キーであり、
返信の In-Reply-To と突合する鍵でもある。
外部依存なし（stdlib のみ）。
"""

from __future__ import annotations

from email.utils import make_msgid


def new_message_id() -> str:
    """
    RFC 準拠の Message-ID を発行する。

    書式は手組みせず email.utils.make_msgid() に委ねる。
    一意性は make_msgid が用いる時刻・PID・乱数の組み合わせが担保する。

    Returns:
        角括弧込みの Message-ID（例: "<176...@host>"）
    """
    return make_msgid()


__all__ = ["new_message_id"]
