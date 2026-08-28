# tests/adapters/test_ledger_recording_mail.py
"""
LedgerRecordingMail のテスト

Stage 3: 送信経路の合流点を塞ぐ（MailPort デコレータ）

外部送信は一切行わない。fake MailPort + fake LedgerPort で完結させる。
"""

import os
import sys

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from domain.exceptions import MailError
from domain.models import LedgerRecord, ReplyRecord
from usecases.ports import LedgerPort, MailPort

RECIPIENT = "recipient@example.com"


class FakeMail:
    """
    fake MailPort。

    YagmailAdapter と同じ内部構造を持つ（send_custom / test が自分の send を呼ぶ）。
    デコレータの二重記録を検出するには、この内部呼び出しの再現が要る。
    """

    def __init__(self, error: Exception | None = None) -> None:
        self.send_calls: list[dict[str, object]] = []
        self.send_custom_calls: list[dict[str, object]] = []
        self.test_calls = 0
        self._error = error

    def send(
        self, to: str, subject: str, body: str, *, message_id: str | None = None
    ) -> None:
        self.send_calls.append(
            {"to": to, "subject": subject, "body": body, "message_id": message_id}
        )
        if self._error:
            raise self._error

    def test(self) -> None:
        self.test_calls += 1
        self.send(to=RECIPIENT, subject="Essay System Test", body="<p>test</p>")

    def send_custom(
        self, subject: str, content: str, *, message_id: str | None = None
    ) -> None:
        self.send_custom_calls.append(
            {"subject": subject, "content": content, "message_id": message_id}
        )
        self.send(to=RECIPIENT, subject=subject, body=content, message_id=message_id)


class FakeLedger:
    """fake LedgerPort（記録内容のみ保持）"""

    def __init__(self) -> None:
        self.records: list[LedgerRecord] = []
        self.bodies: list[str] = []

    def record_sent(
        self,
        message_id: str,
        sent_at: str,
        subject: str,
        recipient: str,
        body: str,
    ) -> LedgerRecord | None:
        if any(r.message_id == message_id for r in self.records):
            return None
        record = LedgerRecord(
            message_id=message_id,
            sent_at=sent_at,
            subject=subject,
            recipient=recipient,
            body_file="sent/fake.md",
        )
        self.records.append(record)
        self.bodies.append(body)
        return record

    def load_records(self) -> list[LedgerRecord]:
        return list(self.records)

    def load_sent_bodies(self) -> list[str]:
        return list(self.bodies)

    def append_reply(self, reply: ReplyRecord) -> bool:
        return True

    def load_replies(self) -> list[ReplyRecord]:
        return []


@pytest.fixture
def inner():
    """fake MailPort"""
    return FakeMail()


@pytest.fixture
def ledger():
    """fake LedgerPort"""
    return FakeLedger()


@pytest.fixture
def mail(inner, ledger):
    """台帳記録デコレータでラップした fake"""
    from adapters.mail.ledger_recording_mail import LedgerRecordingMail

    return LedgerRecordingMail(inner, ledger, RECIPIENT)


class TestProtocolConformance:
    """Protocol 準拠"""

    def test_fakes_conform_to_ports(self, inner, ledger):
        """fake 自身が Port に準拠する（テストが本物と同じ形を測っている保証）"""
        assert isinstance(inner, MailPort)
        assert isinstance(ledger, LedgerPort)

    def test_decorator_conforms_to_mail_port(self, mail):
        """デコレータが MailPort に準拠する（呼び出し側の修正がゼロで済む根拠）"""
        assert isinstance(mail, MailPort)


class TestRecording:
    """記録の発生"""

    def test_send_custom_records_one_row(self, mail, inner, ledger):
        """send_custom 1 回につき台帳は 1 行、send の委譲は 1 回"""
        mail.send_custom("日々の雑感", "本文\n二行目")

        assert len(ledger.records) == 1
        assert len(inner.send_custom_calls) == 1
        assert len(inner.send_calls) == 1

    def test_send_custom_records_subject_recipient_and_body(self, mail, ledger):
        """send_custom の記録内容（宛先はデコレータが持つ既定の受信者）"""
        mail.send_custom("日々の雑感", "本文")

        record = ledger.records[0]
        assert record.subject == "日々の雑感"
        assert record.recipient == RECIPIENT
        assert ledger.bodies[0] == "本文"

    def test_send_records_one_row(self, mail, ledger):
        """send 1 回につき台帳は 1 行"""
        mail.send(to="other@example.com", subject="件名", body="本文")

        assert len(ledger.records) == 1
        assert ledger.records[0].recipient == "other@example.com"

    def test_send_with_empty_to_records_default_recipient(self, mail, ledger):
        """to が空なら既定の受信者を記録する（YagmailAdapter の宛先解決と揃える）"""
        mail.send(to="", subject="件名", body="本文")

        assert ledger.records[0].recipient == RECIPIENT

    def test_sent_at_is_iso8601(self, mail, ledger):
        """sent_at は ISO 8601（採番はデコレータの責務）"""
        from datetime import datetime

        mail.send_custom("件名", "本文")

        # 解釈できなければ ValueError で落ちる
        datetime.fromisoformat(ledger.records[0].sent_at)


class TestNoDoubleRecording:
    """二重記録の不在（この Stage の要）"""

    def test_inner_self_send_bypasses_decorator(self, mail, inner, ledger):
        """
        inner の send_custom が内部で呼ぶ self.send は inner 側のメソッドであり、
        デコレータを通らない。この性質が崩れると台帳が 2 行になる。
        """
        mail.send_custom("件名", "本文")

        assert len(ledger.records) == 1
        # inner の send は「内部呼び出し 1 回」のみ（デコレータ経由の重複がない）
        assert len(inner.send_calls) == 1

    def test_test_email_is_not_recorded(self, mail, inner, ledger):
        """test() は台帳に載らない（委譲のみ）"""
        mail.test()

        assert inner.test_calls == 1
        assert ledger.records == []


class TestFailureIsNotRecorded:
    """失敗時の扱い"""

    def test_send_failure_leaves_ledger_empty_and_propagates(self, ledger):
        """send が例外で終われば台帳は空のまま、例外はそのまま伝播する"""
        from adapters.mail.ledger_recording_mail import LedgerRecordingMail

        failing = FakeMail(error=MailError("boom"))
        mail = LedgerRecordingMail(failing, ledger, RECIPIENT)

        with pytest.raises(MailError):
            mail.send(to=RECIPIENT, subject="件名", body="本文")

        assert ledger.records == []

    def test_send_custom_failure_leaves_ledger_empty_and_propagates(self, ledger):
        """send_custom が例外で終わっても同じ"""
        from adapters.mail.ledger_recording_mail import LedgerRecordingMail

        failing = FakeMail(error=MailError("boom"))
        mail = LedgerRecordingMail(failing, ledger, RECIPIENT)

        with pytest.raises(MailError):
            mail.send_custom("件名", "本文")

        assert ledger.records == []


class TestMessageId:
    """Message-ID の一致"""

    def test_send_passes_generated_id_matching_ledger(self, mail, inner, ledger):
        """send: inner が受け取った Message-ID と台帳の値が一致する"""
        mail.send(to=RECIPIENT, subject="件名", body="本文")

        passed = inner.send_calls[0]["message_id"]
        assert passed is not None
        assert passed.startswith("<") and passed.endswith(">")
        assert ledger.records[0].message_id == passed

    def test_send_custom_passes_generated_id_matching_ledger(self, mail, inner, ledger):
        """send_custom: inner が受け取った Message-ID と台帳の値が一致する"""
        mail.send_custom("件名", "本文")

        passed = inner.send_custom_calls[0]["message_id"]
        assert passed is not None
        assert ledger.records[0].message_id == passed
        # 内部委譲された send にも同じ値が渡る
        assert inner.send_calls[0]["message_id"] == passed

    def test_explicit_message_id_is_honored(self, mail, inner, ledger):
        """呼び出し側が Message-ID を指定した場合はそれを使う"""
        mail.send(
            to=RECIPIENT,
            subject="件名",
            body="本文",
            message_id="<given@example.com>",
        )

        assert inner.send_calls[0]["message_id"] == "<given@example.com>"
        assert ledger.records[0].message_id == "<given@example.com>"

    def test_consecutive_sends_get_distinct_ids(self, mail, ledger):
        """連続送信で Message-ID が衝突しない"""
        mail.send_custom("件名1", "本文1")
        mail.send_custom("件名2", "本文2")

        assert len({r.message_id for r in ledger.records}) == 2
