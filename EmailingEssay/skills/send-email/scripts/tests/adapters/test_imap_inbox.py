# tests/adapters/test_imap_inbox.py
"""
IMAP 受信箱アダプターのテスト

実接続は行わない。imaplib.IMAP4_SSL を差し替えたうえで、
socket も塞いで「万一の実接続」をテスト側で構造的に禁止する。

Stage 4: IMAP による返信の取り込み
"""

import base64
import imaplib
import os
import socket
import sys
from unittest.mock import patch

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from adapters.mail.imap_inbox import (
    ImapInboxAdapter,
    extract_body,
    parse_candidate,
    parse_fetch_response,
    parse_search_response,
    quote_imap_string,
)
from domain.config import Config
from domain.exceptions import MailError
from domain.models import UNTRUSTED_EXTERNAL_DATA

PASSWORD = "abcdefghijklmnop"
SENDER = "essay@example.com"
RECIPIENT = "reader@example.com"

HEADER_BYTES = (
    b"From: Reader <reader@example.com>\r\n"
    b"Date: Fri, 28 Aug 2026 10:00:00 +0900\r\n"
    b"Message-ID: <reply-1@mail.example.com>\r\n"
    b"In-Reply-To: <abc123@essay.local>\r\n"
    b"Subject: Re: nikki\r\n"
    b"\r\n"
)

HEADER_NO_IN_REPLY_TO = (
    b"From: Reader <reader@example.com>\r\n"
    b"Message-ID: <notice-1@mail.example.com>\r\n"
    b"Subject: unrelated\r\n"
    b"\r\n"
)

MESSAGE_BYTES = HEADER_BYTES + "ありがとう\n".encode()

# 受信側 MTA（Gmail）が最上部に付けた本物と、送信者が本文と一緒に下へ
# 仕込んだ偽装。信用できるのは前者だけ。
TOP_AUTH_RESULTS = "mx.google.com; dkim=pass header.i=@example.com; spf=pass"
FORGED_AUTH_RESULTS = "evil.example; dkim=pass; spf=pass"

HEADER_TWO_AUTH_RESULTS = (
    b"Authentication-Results: " + TOP_AUTH_RESULTS.encode() + b"\r\n"
    b"From: Reader <reader@example.com>\r\n"
    b"Message-ID: <reply-1@mail.example.com>\r\n"
    b"In-Reply-To: <abc123@essay.local>\r\n"
    b"Authentication-Results: " + FORGED_AUTH_RESULTS.encode() + b"\r\n"
    b"\r\n"
)


@pytest.fixture(autouse=True)
def _block_network(monkeypatch):
    """このモジュールのテストからの実接続を構造的に禁止する"""

    def _blocked(*args, **kwargs):
        raise AssertionError("network access attempted in tests")

    monkeypatch.setattr(socket, "create_connection", _blocked)
    monkeypatch.setattr(socket, "socket", _blocked)


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    """認証情報（実在しないダミー）"""
    monkeypatch.setenv("ESSAY_SENDER_EMAIL", SENDER)
    monkeypatch.setenv("ESSAY_APP_PASSWORD", PASSWORD)
    monkeypatch.setenv("ESSAY_RECIPIENT_EMAIL", RECIPIENT)
    Config.reset()
    yield
    Config.reset()


class FakeImap:
    """imaplib.IMAP4_SSL の fake（ソケットを開かない）"""

    def __init__(
        self,
        search=("OK", [b"1 2"]),
        headers=None,
        bodies=None,
        login_error=None,
        select_status="OK",
    ):
        self._search = search
        self._headers = headers or (
            "OK",
            [
                (b"1 (UID 1 BODY[HEADER] {10}", HEADER_BYTES),
                b")",
                (b"2 (UID 2 BODY[HEADER] {10}", HEADER_NO_IN_REPLY_TO),
                b")",
            ],
        )
        self._bodies = bodies or (
            "OK",
            [(b"1 (UID 1 BODY[] {10}", MESSAGE_BYTES), b")"],
        )
        self._login_error = login_error
        self._select_status = select_status
        self.commands = []
        self.logged_out = False

    def login(self, user, password):
        if self._login_error is not None:
            raise self._login_error
        self.commands.append(("login", user))
        return ("OK", [b"logged in"])

    def select(self, mailbox, readonly=False):
        self.commands.append(("select", mailbox, readonly))
        return (self._select_status, [b"1"])

    def uid(self, command, *args):
        self.commands.append((command, *args))
        if command == "SEARCH":
            return self._search
        if "HEADER" in args[-1]:
            return self._headers
        return self._bodies

    def logout(self):
        self.logged_out = True
        return ("BYE", [b"bye"])


def _patched(fake):
    """imaplib.IMAP4_SSL を fake に差し替えるコンテキスト"""
    return patch("adapters.mail.imap_inbox.imaplib.IMAP4_SSL", return_value=fake)


class TestConstruction:
    """初期化（接続はしない）"""

    def test_init_does_not_connect(self):
        """コンストラクタは imaplib に触らない（YagmailAdapter と同じ流儀）"""
        with patch("adapters.mail.imap_inbox.imaplib.IMAP4_SSL") as ctor:
            ImapInboxAdapter()
            ctor.assert_not_called()

    def test_init_requires_credentials(self, monkeypatch):
        """認証情報が欠けていれば MailError"""
        monkeypatch.delenv("ESSAY_SENDER_EMAIL", raising=False)
        monkeypatch.delenv("ESSAY_APP_PASSWORD", raising=False)
        monkeypatch.delenv("ESSAY_RECIPIENT_EMAIL", raising=False)
        Config.reset()

        with pytest.raises(MailError):
            ImapInboxAdapter()


class TestFetchReplies:
    """fetch_replies（fake クライアント経由）"""

    def test_returns_candidates_with_body(self):
        """In-Reply-To を持つメールだけ本文を取りに行き、候補として返す"""
        fake = FakeImap()
        with _patched(fake):
            replies = ImapInboxAdapter().fetch_replies(RECIPIENT)

        assert len(replies) == 1
        assert replies[0].message_id == "<reply-1@mail.example.com>"
        assert replies[0].in_reply_to == "<abc123@essay.local>"
        assert replies[0].body.strip() == "ありがとう"
        assert replies[0].content_class == UNTRUSTED_EXTERNAL_DATA

    def test_searches_inbox_readonly_by_sender(self):
        """INBOX を readonly で開き、From で絞る（横断検索をしない）"""
        fake = FakeImap()
        with _patched(fake):
            ImapInboxAdapter().fetch_replies(RECIPIENT)

        assert ("select", "INBOX", True) in fake.commands
        assert ("SEARCH", "FROM", '"reader@example.com"') in fake.commands

    def test_uses_peek_so_messages_stay_unread(self):
        """BODY.PEEK を使う（既読フラグを立てない）"""
        fake = FakeImap()
        with _patched(fake):
            ImapInboxAdapter().fetch_replies(RECIPIENT)

        fetch_specs = [c[-1] for c in fake.commands if c[0] == "FETCH"]
        assert fetch_specs == ["(BODY.PEEK[HEADER])", "(BODY.PEEK[])"]

    def test_empty_search_skips_fetch(self):
        """該当なしなら本文取得へ進まない"""
        fake = FakeImap(search=("OK", [b""]))
        with _patched(fake):
            assert ImapInboxAdapter().fetch_replies(RECIPIENT) == []

        assert not [c for c in fake.commands if c[0] == "FETCH"]

    def test_no_in_reply_to_skips_body_fetch(self):
        """In-Reply-To を持つメールが無ければ本文を取りに行かない"""
        fake = FakeImap(
            headers=(
                "OK",
                [(b"2 (UID 2 BODY[HEADER] {10}", HEADER_NO_IN_REPLY_TO), b")"],
            )
        )
        with _patched(fake):
            assert ImapInboxAdapter().fetch_replies(RECIPIENT) == []

        fetch_specs = [c[-1] for c in fake.commands if c[0] == "FETCH"]
        assert fetch_specs == ["(BODY.PEEK[HEADER])"]

    def test_logs_out_after_success(self):
        """成功時にログアウトする"""
        fake = FakeImap()
        with _patched(fake):
            ImapInboxAdapter().fetch_replies(RECIPIENT)

        assert fake.logged_out is True


class TestErrorHandling:
    """失敗の見え方（ops-rules 1）"""

    def test_authentication_failure_hides_password(self):
        """認証失敗は MailError。パスワードも例外本文も表に出さない"""
        fake = FakeImap(
            login_error=imaplib.IMAP4.error(
                f"b'[AUTHENTICATIONFAILED] Invalid credentials {PASSWORD}'"
            )
        )
        with _patched(fake), pytest.raises(MailError) as exc:
            ImapInboxAdapter().fetch_replies(RECIPIENT)

        assert PASSWORD not in str(exc.value)
        assert "AUTHENTICATIONFAILED" not in str(exc.value)
        assert "authentication" in str(exc.value).lower()

    def test_connection_failure_raises_mailerror(self):
        """接続失敗は MailError（生の OSError を上げない）"""
        with (
            patch(
                "adapters.mail.imap_inbox.imaplib.IMAP4_SSL",
                side_effect=OSError("unreachable"),
            ),
            pytest.raises(MailError) as exc,
        ):
            ImapInboxAdapter().fetch_replies(RECIPIENT)

        assert PASSWORD not in str(exc.value)

    def test_select_failure_raises_mailerror(self):
        """SELECT 失敗は MailError"""
        fake = FakeImap(select_status="NO")
        with _patched(fake), pytest.raises(MailError):
            ImapInboxAdapter().fetch_replies(RECIPIENT)

    def test_search_failure_raises_mailerror(self):
        """SEARCH 失敗は MailError"""
        fake = FakeImap(search=("NO", [b""]))
        with _patched(fake), pytest.raises(MailError):
            ImapInboxAdapter().fetch_replies(RECIPIENT)

    def test_logs_out_even_on_failure(self):
        """途中で落ちてもログアウトする"""
        fake = FakeImap(search=("NO", [b""]))
        with _patched(fake), pytest.raises(MailError):
            ImapInboxAdapter().fetch_replies(RECIPIENT)

        assert fake.logged_out is True

    def test_rejects_unsafe_sender(self):
        """IMAP 文字列を壊す差出人はコマンドを組み立てる前に弾く"""
        fake = FakeImap()
        with _patched(fake), pytest.raises(MailError):
            ImapInboxAdapter().fetch_replies('a@b.com" OR "')


class TestParseCandidate:
    """ヘッダのパース（純粋関数）"""

    def test_extracts_fields(self):
        record = parse_candidate(HEADER_BYTES)

        assert record.message_id == "<reply-1@mail.example.com>"
        assert record.in_reply_to == "<abc123@essay.local>"
        assert record.sender == "Reader <reader@example.com>"
        assert record.received_at.startswith("2026-08-28T10:00:00")
        assert record.body == ""
        assert record.content_class == UNTRUSTED_EXTERNAL_DATA

    def test_unfolds_headers(self):
        """折り返されたヘッダを 1 行に畳む"""
        raw = (
            b"From: Reader\r\n <reader@example.com>\r\n"
            b"Message-ID: <r1@mail>\r\n"
            b"In-Reply-To:\r\n <abc123@essay.local>\r\n\r\n"
        )
        record = parse_candidate(raw)

        assert record.in_reply_to == "<abc123@essay.local>"
        assert record.sender == "Reader <reader@example.com>"

    def test_missing_headers_become_empty(self):
        record = parse_candidate(b"Subject: nothing\r\n\r\n")

        assert record.message_id == ""
        assert record.in_reply_to == ""
        assert record.sender == ""
        assert record.auth_results == ""

    def test_unfolds_authentication_results(self):
        """折り返された Authentication-Results も 1 行に畳む"""
        raw = (
            b"Message-ID: <r1@mail>\r\n"
            b"Authentication-Results: mx.google.com;\r\n dkim=pass;\r\n spf=pass\r\n\r\n"
        )

        assert parse_candidate(raw).auth_results == "mx.google.com; dkim=pass; spf=pass"

    def test_takes_only_the_topmost_authentication_results(self):
        """AR が複数あれば最上部の 1 本だけを採る（下方は送信者が仕込める）"""
        record = parse_candidate(HEADER_TWO_AUTH_RESULTS)

        assert record.auth_results == TOP_AUTH_RESULTS
        assert "evil.example" not in record.auth_results

    def test_unparsable_date_falls_back_to_now(self):
        """Date が壊れていても落ちない"""
        raw = b"Message-ID: <r1@mail>\r\nDate: not-a-date\r\n\r\n"

        assert parse_candidate(raw).received_at


class TestExtractBody:
    """本文の取り出し（純粋関数）"""

    def test_plain_utf8(self):
        assert extract_body(MESSAGE_BYTES).strip() == "ありがとう"

    def test_iso_2022_jp_is_decoded(self):
        raw = (
            b"MIME-Version: 1.0\r\n"
            b"Content-Type: text/plain; charset=ISO-2022-JP\r\n"
            b"Content-Transfer-Encoding: base64\r\n\r\n"
            + base64.b64encode("ありがとう".encode("iso-2022-jp"))
        )

        assert extract_body(raw).strip() == "ありがとう"

    def test_multipart_prefers_text_plain(self):
        raw = (
            b"MIME-Version: 1.0\r\n"
            b'Content-Type: multipart/alternative; boundary="B"\r\n\r\n'
            b"--B\r\n"
            b"Content-Type: text/html; charset=utf-8\r\n\r\n"
            b"<p>html</p>\r\n"
            b"--B\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n\r\n"
            b"plain text\r\n"
            b"--B--\r\n"
        )

        assert extract_body(raw).strip() == "plain text"

    def test_unknown_charset_falls_back(self):
        """未知の charset でも落ちず、読める形で返す"""
        raw = b"Content-Type: text/plain; charset=x-unknown-charset\r\n\r\nhello\r\n"

        assert "hello" in extract_body(raw)

    def test_html_only_yields_empty(self):
        raw = b"Content-Type: text/html; charset=utf-8\r\n\r\n<p>html</p>\r\n"

        assert extract_body(raw) == ""


class TestResponseParsers:
    """IMAP レスポンスの畳み込み（純粋関数）"""

    def test_search_response(self):
        assert parse_search_response([b"1 2 3"]) == ["1", "2", "3"]

    def test_search_response_empty(self):
        assert parse_search_response([b""]) == []
        assert parse_search_response([None]) == []

    def test_fetch_response_maps_uid_to_payload(self):
        data = [
            (b"1 (UID 41 BODY[HEADER] {10}", b"header-a"),
            b")",
            (b"2 (UID 42 BODY[HEADER] {10}", b"header-b"),
            b")",
        ]

        assert parse_fetch_response(data) == {"41": b"header-a", "42": b"header-b"}

    def test_fetch_response_skips_unparsable_items(self):
        data = [b")", (b"no uid here", b"payload"), ("not", "bytes")]

        assert parse_fetch_response(data) == {}


class TestQuoteImapString:
    """IMAP 文字列の引用（コマンド組み立ての防御）"""

    def test_quotes_plain_address(self):
        assert quote_imap_string("a@b.com") == '"a@b.com"'

    @pytest.mark.parametrize(
        "value", ['a@b.com" OR "', "a@b.com\\", "a@b.com\r\nX", "a@b.com\n"]
    )
    def test_rejects_unsafe_values(self, value):
        with pytest.raises(MailError):
            quote_imap_string(value)


class TestNetworkGuard:
    """テスト自身が実接続していないことの担保"""

    def test_socket_is_blocked(self):
        """autouse fixture が socket を塞いでいる"""
        with pytest.raises(AssertionError):
            socket.create_connection(("imap.gmail.com", 993))
