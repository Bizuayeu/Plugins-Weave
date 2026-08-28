# tests/usecases/test_ingest_replies.py
"""
返信取り込みユースケースのテスト

fake InboxPort と実 LedgerStorageAdapter（tmp_path）で、
取り込み判定と冪等性を検証する。ネットワークには一切触れない。

Stage 4: IMAP による返信の取り込み
"""

import os
import sys

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from adapters.storage.ledger_storage import LedgerStorageAdapter
from adapters.storage.path_resolver import PathResolverAdapter
from domain.models import UNTRUSTED_EXTERNAL_DATA, ReplyRecord
from usecases.ingest_replies import IngestRepliesUseCase

RECIPIENT = "reader@example.com"
SENDER = "ai@example.com"
SENT_MESSAGE_ID = "<abc123@essay.local>"
SELF_NOTE_MESSAGE_ID = "<note456@essay.local>"


class FakeInbox:
    """InboxPort の fake（受信箱の中身を固定で返す）"""

    def __init__(self, candidates):
        self._candidates = candidates
        self.calls = []

    def fetch_replies(self, sender):
        self.calls.append(sender)
        return list(self._candidates)


def _reply(message_id, in_reply_to, sender, body="ありがとう"):
    """返信候補を作る"""
    return ReplyRecord(
        message_id=message_id,
        in_reply_to=in_reply_to,
        sender=sender,
        received_at="2026-08-28T10:00:00",
        body=body,
    )


@pytest.fixture
def ledger(tmp_path):
    """実ストレージ（tmp_path）に送信済み 1 件を仕込んだ台帳"""
    adapter = LedgerStorageAdapter(PathResolverAdapter(str(tmp_path)))
    adapter.record_sent(
        message_id=SENT_MESSAGE_ID,
        sent_at="2026-08-27T21:00:00",
        subject="日々の雑感",
        recipient=RECIPIENT,
        body="本文",
    )
    return adapter


def _usecase(inbox, ledger):
    return IngestRepliesUseCase(inbox=inbox, ledger=ledger, recipient=RECIPIENT)


class TestAcceptance:
    """取り込み判定（In-Reply-To の突合 ∧ From の照合）"""

    def test_ingests_only_the_matching_reply(self, ledger):
        """一致 / From 違い / In-Reply-To 違いの 3 通 → 取り込むのは 1 通"""
        inbox = FakeInbox(
            [
                _reply("<r1@mail>", SENT_MESSAGE_ID, RECIPIENT),
                _reply("<r2@mail>", SENT_MESSAGE_ID, "stranger@example.com"),
                _reply("<r3@mail>", "<unknown@essay.local>", RECIPIENT),
            ]
        )

        ingested = _usecase(inbox, ledger).fetch()

        assert [r.message_id for r in ingested] == ["<r1@mail>"]
        assert [r.message_id for r in ledger.load_replies()] == ["<r1@mail>"]

    def test_accepts_folded_and_unbracketed_in_reply_to(self, ledger):
        """折り返し・角括弧なしの In-Reply-To も突合できる"""
        inbox = FakeInbox([_reply("<r1@mail>", "\r\n abc123@essay.local", RECIPIENT)])

        assert len(_usecase(inbox, ledger).fetch()) == 1

    def test_accepts_display_name_and_differing_case(self, ledger):
        """From が表示名つき・大文字小文字違いでも照合できる"""
        inbox = FakeInbox(
            [_reply("<r1@mail>", SENT_MESSAGE_ID, "Reader <READER@Example.com>")]
        )

        assert len(_usecase(inbox, ledger).fetch()) == 1

    def test_drops_candidate_without_message_id(self, ledger):
        """Message-ID を欠く候補は落とす（冪等性の鍵が立たないため）"""
        inbox = FakeInbox([_reply("", SENT_MESSAGE_ID, RECIPIENT)])

        assert _usecase(inbox, ledger).fetch() == []
        assert ledger.load_replies() == []

    def test_drops_candidate_without_sender(self, ledger):
        """From を欠く候補は落とす"""
        inbox = FakeInbox([_reply("<r1@mail>", SENT_MESSAGE_ID, "")])

        assert _usecase(inbox, ledger).fetch() == []

    def test_empty_inbox_yields_nothing(self, ledger):
        """受信箱が空でも落ちない"""
        assert _usecase(FakeInbox([]), ledger).fetch() == []


class TestSelfAddressedNotes:
    """自分宛の書き置き（CLI の --to-self）は返信として取り込まない"""

    @pytest.fixture
    def ledger_with_note(self, ledger):
        """自分宛の書き置きを 1 件足した台帳"""
        ledger.record_sent(
            message_id=SELF_NOTE_MESSAGE_ID,
            sent_at="2026-08-27T22:00:00",
            subject="書き置き",
            recipient=SENDER,
            body="沈黙の日のメモ",
        )
        return ledger

    def test_note_from_self_is_not_ingested(self, ledger_with_note):
        """In-Reply-To は台帳と合っても、From が自分なら取り込まない"""
        inbox = FakeInbox([_reply("<n1@mail>", SELF_NOTE_MESSAGE_ID, SENDER)])

        assert _usecase(inbox, ledger_with_note).fetch() == []
        assert ledger_with_note.load_replies() == []

    def test_same_thread_from_reader_is_ingested(self, ledger_with_note):
        """同じ書き置きへの反響でも From が読み手なら取り込む（弾いたのは From）"""
        inbox = FakeInbox([_reply("<n2@mail>", SELF_NOTE_MESSAGE_ID, RECIPIENT)])

        assert len(_usecase(inbox, ledger_with_note).fetch()) == 1


class TestIdempotency:
    """同じ返信を二度取り込まない"""

    def test_second_fetch_adds_nothing(self, ledger):
        """2 回目の fetch で返信ファイルが増えない"""
        inbox = FakeInbox([_reply("<r1@mail>", SENT_MESSAGE_ID, RECIPIENT)])
        usecase = _usecase(inbox, ledger)

        first = usecase.fetch()
        second = usecase.fetch()

        assert len(first) == 1
        assert second == []
        assert len(ledger.load_replies()) == 1


class TestFencing:
    """外部入力としての素性表明（ops-rules 7）"""

    def test_stored_reply_keeps_content_class(self, ledger):
        """保存された返信は content_class を持つ"""
        inbox = FakeInbox([_reply("<r1@mail>", SENT_MESSAGE_ID, RECIPIENT)])

        _usecase(inbox, ledger).fetch()

        stored = ledger.load_replies()[0]
        assert stored.content_class == UNTRUSTED_EXTERNAL_DATA
        assert stored.body == "ありがとう"


class TestInboxQuery:
    """受信箱への問い合わせ方"""

    def test_passes_recipient_as_sender_filter(self, ledger):
        """自分が投げた球の跳ね返りだけを拾う（受信箱の横断検索をしない）"""
        inbox = FakeInbox([])

        _usecase(inbox, ledger).fetch()

        assert inbox.calls == [RECIPIENT]


class TestNormalizeMessageId:
    """Message-ID 正規化"""

    def test_strips_whitespace_and_brackets(self):
        from usecases.ingest_replies import normalize_message_id

        assert normalize_message_id("<a@b>") == "a@b"
        assert normalize_message_id("\r\n <a@b>\t") == "a@b"
        assert normalize_message_id("a@b") == "a@b"
