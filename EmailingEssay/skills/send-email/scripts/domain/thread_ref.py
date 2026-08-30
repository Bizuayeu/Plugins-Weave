# domain/thread_ref.py
"""
スレッド接続

Entities層: 送信をどの便に紐づけるかを表し、RFC 5322 のスレッドヘッダ
（In-Reply-To / References）へ落とす。
外部依存なし（stdlib のみ）。

返信は In-Reply-To で台帳の便に紐づくのに、便の側は何にも紐づいていなかった
——紐が片道だったのを両方向にするための型。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .models import ReplyRecord

__all__ = ["ThreadRef", "thread_ref_for"]


def _bracketed(message_id: str) -> str:
    """
    Message-ID をヘッダに載る `<...>` 形へ揃える。

    折り返しの空白と角括弧の有無は経路によって揺れるが、ヘッダ値としては
    角括弧が必須（RFC 5322 の msg-id）。突合用の正規化（角括弧を剥ぐ）とは
    逆向きの操作なので、こちらで一元化する。

    Args:
        message_id: 生の Message-ID（角括弧の有無・折り返しを問わない）

    Returns:
        角括弧込みの Message-ID（中身が空なら空文字）
    """
    core = "".join(message_id.split()).strip("<>")
    return f"<{core}>" if core else ""


@dataclass(frozen=True)
class ThreadRef:
    """
    送信の紐づけ先。

    in_reply_to が直接の親、references がスレッドの鎖。どちらも角括弧の
    有無を問わず受け取り、ヘッダへ載せる時に揃える。
    """

    in_reply_to: str
    references: str = ""

    def headers(self) -> dict[str, str]:
        """
        スレッドヘッダへ落とす。

        Returns:
            In-Reply-To / References の辞書。紐づけ先が無ければ空の辞書
            （ヘッダを 1 本も足さない＝新規スレッドとして立つ）
        """
        parent = _bracketed(self.in_reply_to)
        if not parent:
            return {}
        chain = " ".join(
            b for b in (_bracketed(r) for r in self.references.split()) if b
        )
        return {"In-Reply-To": parent, "References": chain or parent}


def thread_ref_for(message_id: str, replies: Sequence[ReplyRecord]) -> ThreadRef:
    """
    紐づけ先の Message-ID から ThreadRef を組む。

    取り込み済みの返信を指した場合は、その返信が答えている便まで References を
    一段遡らせる（台帳が既に持っている情報だけで鎖を組む）。台帳に無い相手は
    親 1 本だけにする——鎖を推測で伸ばさない。

    cc-defer: References は 2 段まで（返信自身の References を保存していない）。
    3 段以上のスレッドを客先の client が繋げなくなったら ReplyRecord へ
    references を持たせる

    Args:
        message_id: 紐づけ先の Message-ID（角括弧の有無を問わない）
        replies: 取り込み済みの返信一覧（鎖を遡る材料）

    Returns:
        組み上がった ThreadRef（message_id が空なら紐づけ無しの ThreadRef）
    """
    target = _bracketed(message_id)
    if not target:
        return ThreadRef(in_reply_to="")

    for reply in replies:
        if _bracketed(reply.message_id) == target:
            parent = _bracketed(reply.in_reply_to)
            return ThreadRef(
                in_reply_to=target, references=f"{parent} {target}".strip()
            )
    return ThreadRef(in_reply_to=target)
