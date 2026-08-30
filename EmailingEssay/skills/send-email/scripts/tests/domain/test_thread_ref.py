# tests/domain/test_thread_ref.py
"""
スレッド接続のテスト

ThreadRef / thread_ref_for のテスト。
"""

import os
import sys

# scriptsディレクトリをパスに追加
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from domain.models import ReplyRecord
from domain.thread_ref import ThreadRef, thread_ref_for

ESSAY_ID = "<essay-1@essay.local>"
REPLY_ID = "<reply-1@mail.gmail.com>"


def _reply(message_id=REPLY_ID, in_reply_to=ESSAY_ID):
    return ReplyRecord(
        message_id=message_id,
        in_reply_to=in_reply_to,
        sender="reader@example.com",
        received_at="2026-08-30T21:36:18+09:00",
        body="ありがとう",
    )


class TestThreadRefHeaders:
    """ThreadRef.headers のテスト"""

    def test_emits_both_thread_headers(self):
        """In-Reply-To と References の 2 本を返す"""
        headers = ThreadRef(in_reply_to=REPLY_ID, references=f"{ESSAY_ID} {REPLY_ID}")

        assert headers.headers() == {
            "In-Reply-To": REPLY_ID,
            "References": f"{ESSAY_ID} {REPLY_ID}",
        }

    def test_brackets_a_bare_message_id(self):
        """角括弧なしで渡されてもヘッダには <...> で載る（RFC 5322 の msg-id）"""
        headers = ThreadRef(in_reply_to="reply-1@mail.gmail.com").headers()

        assert headers["In-Reply-To"] == REPLY_ID
        assert headers["References"] == REPLY_ID

    def test_folded_value_is_flattened(self):
        """折り返しの空白が混ざっていても 1 本に畳んで載せる"""
        headers = ThreadRef(in_reply_to="<reply-1@\r\n mail.gmail.com>").headers()

        assert headers["In-Reply-To"] == REPLY_ID

    def test_references_defaults_to_the_parent(self):
        """References 未指定なら親 1 本だけを載せる"""
        headers = ThreadRef(in_reply_to=REPLY_ID).headers()

        assert headers["References"] == REPLY_ID

    def test_empty_ref_emits_no_headers(self):
        """紐づけ先が無ければヘッダを 1 本も足さない（新規スレッドとして立つ）"""
        assert ThreadRef(in_reply_to="").headers() == {}

    def test_blank_reference_tokens_are_dropped(self):
        """References の空トークンは落ちる（空の <> をヘッダに残さない）"""
        headers = ThreadRef(in_reply_to=REPLY_ID, references="  <>  ").headers()

        assert headers["References"] == REPLY_ID


class TestThreadRefFor:
    """thread_ref_for のテスト"""

    def test_known_reply_chains_back_to_the_essay(self):
        """取り込み済みの返信を指すと、その返信が答えた便まで References が遡る"""
        ref = thread_ref_for(REPLY_ID, [_reply()])

        assert ref.in_reply_to == REPLY_ID
        assert ref.references == f"{ESSAY_ID} {REPLY_ID}"

    def test_matches_regardless_of_brackets(self):
        """角括弧の有無は突合に影響しない"""
        ref = thread_ref_for("reply-1@mail.gmail.com", [_reply()])

        assert ref.references == f"{ESSAY_ID} {REPLY_ID}"

    def test_unknown_id_keeps_the_parent_alone(self):
        """台帳に無い相手なら親 1 本だけ（推測で鎖を伸ばさない）"""
        ref = thread_ref_for("<stranger@example.com>", [_reply()])

        assert ref.in_reply_to == "<stranger@example.com>"
        assert ref.headers()["References"] == "<stranger@example.com>"

    def test_reply_without_parent_chains_to_itself_only(self):
        """親を持たない返信レコードなら鎖は自分 1 本"""
        ref = thread_ref_for(REPLY_ID, [_reply(in_reply_to="")])

        assert ref.references == REPLY_ID

    def test_empty_id_yields_no_headers(self):
        """空文字を渡したら紐づけ無し"""
        assert thread_ref_for("", [_reply()]).headers() == {}
