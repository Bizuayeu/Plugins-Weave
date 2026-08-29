# adapters/mail/imap_inbox.py
"""
IMAP 受信箱アダプター

標準ライブラリの imaplib で INBOX を読み、返信候補を取り出す（InboxPort 実装）。
新規依存はゼロ。ホストは imap.gmail.com 固定——送信側が yagmail = Gmail 前提
なので、受信だけ汎用化しても組み合わせが成立しない（新規環境変数は増やさない）。

取り方は「INBOX を readonly で開き、From で絞った分のヘッダを一度に取り、
In-Reply-To を持つものだけ本文を取りに行く」。サーバ側の SEARCH HEADER には
依存しない（Gmail での挙動が渋いため）。突合と受け入れ判定は UseCase の領分で、
ここが返すのはあくまで候補。

Stage 4: IMAP による返信の取り込み
"""

from __future__ import annotations

import email
import imaplib
import re
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Any

from domain.exceptions import MailError
from domain.models import ReplyRecord
from frameworks.logging_config import get_logger

logger = get_logger("inbox")

__all__ = [
    "IMAP_HOST",
    "MAILBOX",
    "ImapInboxAdapter",
    "extract_body",
    "parse_candidate",
    "parse_fetch_response",
    "parse_search_response",
    "quote_imap_string",
]

# 送信側（yagmail）が Gmail 前提のため、受信も Gmail 固定
IMAP_HOST = "imap.gmail.com"
MAILBOX = "INBOX"

# 既読フラグを立てずに読む（PEEK）。返信は人が読むものでもある
HEADER_SPEC = "(BODY.PEEK[HEADER])"
MESSAGE_SPEC = "(BODY.PEEK[])"

_UID_RE = re.compile(rb"UID (\d+)")

# IMAP の quoted string を壊す文字（引用符・エスケープ・制御文字）
_UNSAFE_IMAP_CHARS = re.compile(r'["\\\x00-\x1f\x7f]')


# =============================================================================
# 純粋関数（ネットワークに触れない部分）
# =============================================================================


def quote_imap_string(value: str) -> str:
    """
    IMAP コマンドに載せる文字列を引用する。

    エスケープで凌がず、危険な文字を含む値はコマンドを組み立てる前に弾く
    （検索語は設定由来だが、コマンド組み立てに外部値を素で流さない）。

    Args:
        value: 引用したい文字列（差出人アドレス）

    Returns:
        引用済み文字列

    Raises:
        MailError: IMAP 文字列として安全に載せられない値の場合
    """
    if not value or _UNSAFE_IMAP_CHARS.search(value):
        raise MailError("Unsafe address for IMAP search")
    return f'"{value}"'


def parse_search_response(data: Sequence[Any]) -> list[str]:
    """
    SEARCH レスポンスから UID の一覧を取り出す。

    Args:
        data: imaplib が返した data 部（例: [b"1 2 3"]）

    Returns:
        UID の文字列リスト
    """
    uids: list[str] = []
    for item in data:
        if isinstance(item, bytes):
            uids.extend(token.decode() for token in item.split())
    return uids


def parse_fetch_response(data: Sequence[Any]) -> dict[str, bytes]:
    """
    FETCH レスポンスを UID → 生バイト列の対応へ畳む。

    imaplib は (prefix, payload) のタプルと b")" を交互に返す。prefix に
    含まれる UID で対応づける（並び順に頼らない）。

    Args:
        data: imaplib が返した data 部

    Returns:
        UID をキーとした生バイト列の辞書（読めない項目は捨てる）
    """
    result: dict[str, bytes] = {}
    for item in data:
        if not isinstance(item, tuple) or len(item) < 2:
            continue
        prefix, payload = item[0], item[1]
        if not isinstance(prefix, bytes) or not isinstance(payload, bytes):
            continue
        match = _UID_RE.search(prefix)
        if match is None:
            continue
        result[match.group(1).decode()] = payload
    return result


def _unfold(value: str) -> str:
    """折り返し（CRLF + 空白）を潰してヘッダ値を 1 行にする。"""
    return " ".join(value.split())


def _header(msg: Message, name: str) -> str:
    """
    ヘッダ値を 1 行に畳んで返す（折り返しの CRLF + 空白を潰す）。

    MIME デコードは行わない——ReplyRecord.sender は From ヘッダの生値を
    持つ約束であり、宛先照合は parseaddr が担う。
    """
    value = msg.get(name)
    if value is None:
        return ""
    return _unfold(str(value))


def _topmost_header(msg: Message, name: str) -> str:
    """
    同名ヘッダが複数あるとき、最上部の 1 本だけを 1 行に畳んで返す。

    中継は自分の書いたヘッダをメールの最上部に足していくので、最上部が
    最後の中継＝受信側 MTA の 1 本になる。下方にあるものは送信者が自分で
    仕込めるため、差出人検証の根拠にしてはならない。

    Args:
        msg: パース済みメッセージ
        name: ヘッダ名

    Returns:
        最上部のヘッダ値（不在なら空文字）
    """
    values = msg.get_all(name)
    if not values:
        return ""
    return _unfold(str(values[0]))


def parse_candidate(raw_header: bytes) -> ReplyRecord:
    """
    ヘッダ部から返信候補を組み立てる（本文は空のまま）。

    Args:
        raw_header: BODY[HEADER] の生バイト列

    Returns:
        本文未取得の ReplyRecord（content_class は既定の素性表明）
    """
    msg = email.message_from_bytes(raw_header)
    return ReplyRecord(
        message_id=_header(msg, "Message-ID"),
        in_reply_to=_header(msg, "In-Reply-To"),
        sender=_header(msg, "From"),
        received_at=_received_at(msg),
        body="",
        auth_results=_topmost_header(msg, "Authentication-Results"),
    )


def _received_at(msg: Message) -> str:
    """Date ヘッダを ISO 8601 で返す（読めなければ取り込み時刻）。"""
    raw = _header(msg, "Date")
    if raw:
        try:
            return parsedate_to_datetime(raw).isoformat()
        except (TypeError, ValueError):
            logger.debug("Unparsable Date header; falling back to ingestion time")
    return datetime.now().isoformat()


def extract_body(raw_message: bytes) -> str:
    """
    メール全体から最初の text/plain 本文を取り出す。

    文字コードは宣言に従って復号し、読めないバイトは置換する（1 バイトの
    崩れで取り込み全体を落とさない）。text/plain が無ければ空文字。

    Args:
        raw_message: BODY[] の生バイト列

    Returns:
        復号済み本文（無ければ空文字）
    """
    msg = email.message_from_bytes(raw_message)
    for part in msg.walk():
        if part.get_content_type() != "text/plain":
            continue
        if part.get_content_disposition() == "attachment":
            continue
        payload = part.get_payload(decode=True)
        if not isinstance(payload, bytes):
            continue
        charset = part.get_content_charset() or "utf-8"
        try:
            return payload.decode(charset, errors="replace")
        except LookupError:
            logger.debug(f"Unknown charset in reply body: {charset}")
            return payload.decode("utf-8", errors="replace")
    return ""


# =============================================================================
# アダプター（ここだけが実接続を持つ）
# =============================================================================


class ImapInboxAdapter:
    """IMAP を使った受信箱アダプター（InboxPort実装）"""

    def __init__(self) -> None:
        """
        アダプターを初期化する（接続は張らない）。

        Raises:
            MailError: 必要な設定が不足している場合
        """
        from domain.config import Config

        config = Config.load()
        errors = config.validate()
        if errors:
            raise MailError("; ".join(errors))

        # 認証は送信と同じ Gmail アカウント（新規環境変数は増やさない）
        self._user = config.email.sender
        self._password = config.email.password

    def fetch_replies(self, sender: str) -> list[ReplyRecord]:
        """
        指定の差出人から届いた返信候補を取得する。

        Args:
            sender: 差出人アドレス（INBOX の絞り込みに使う）

        Returns:
            返信候補のリスト

        Raises:
            MailError: 接続・認証・取得に失敗した場合
        """
        query = quote_imap_string(sender)
        client = self._login()
        try:
            return self._collect(client, query)
        finally:
            self._logout(client)

    # -------------------------------------------------------------------------
    # 接続
    # -------------------------------------------------------------------------

    def _login(self) -> imaplib.IMAP4_SSL:
        """
        接続してログインする。

        Raises:
            MailError: 接続・認証に失敗した場合（資格情報は表に出さない）
        """
        try:
            client = imaplib.IMAP4_SSL(IMAP_HOST)
        except OSError as e:
            raise MailError(f"IMAP connection failed: {e}") from e

        try:
            client.login(self._user, self._password)
        except imaplib.IMAP4.error as e:
            # サーバ応答をそのまま流さない（資格情報の経路を作らない — ops-rules 1）
            logger.warning("IMAP authentication failed")
            raise MailError(
                "IMAP authentication failed "
                "(check ESSAY_SENDER_EMAIL / ESSAY_APP_PASSWORD, "
                "and that IMAP is enabled on the account)"
            ) from e
        return client

    @staticmethod
    def _logout(client: imaplib.IMAP4_SSL) -> None:
        """ログアウトする（失敗しても取り込み結果を潰さない）。"""
        try:
            client.logout()
        except (OSError, imaplib.IMAP4.error) as e:
            logger.debug(f"IMAP logout failed: {e}")

    # -------------------------------------------------------------------------
    # 取得
    # -------------------------------------------------------------------------

    def _collect(self, client: imaplib.IMAP4_SSL, query: str) -> list[ReplyRecord]:
        """
        INBOX から返信候補を集める。

        ヘッダは一度の FETCH で全件取り（往復は件数によらず 1 回）、本文は
        In-Reply-To を持つものだけ取りに行く。件数上限を置いていないのは、
        根拠のある上限値が無いため。
        cc-defer: 該当メールの全ヘッダを 1 回で取る。件数が実運用で問題に
        なったら SINCE / UID 範囲で絞る

        Args:
            client: ログイン済みクライアント
            query: 引用済みの差出人アドレス

        Returns:
            返信候補のリスト

        Raises:
            MailError: サーバが OK を返さなかった場合
        """
        status, _ = client.select(MAILBOX, readonly=True)
        if status != "OK":
            raise MailError(f"IMAP select failed: {status}")

        status, data = client.uid("SEARCH", "FROM", query)
        if status != "OK":
            raise MailError(f"IMAP search failed: {status}")

        uids = parse_search_response(data)
        if not uids:
            return []

        candidates = {
            uid: parse_candidate(raw)
            for uid, raw in self._fetch(client, uids, HEADER_SPEC).items()
        }
        # In-Reply-To を持たないメールは台帳のどの行とも突合し得ないため取りに行かない
        targets = [uid for uid, c in candidates.items() if c.in_reply_to]
        if not targets:
            return []

        return [
            replace(candidates[uid], body=extract_body(raw))
            for uid, raw in self._fetch(client, targets, MESSAGE_SPEC).items()
            if uid in candidates
        ]

    @staticmethod
    def _fetch(
        client: imaplib.IMAP4_SSL, uids: list[str], spec: str
    ) -> dict[str, bytes]:
        """
        UID 集合に対して 1 回の FETCH を投げる。

        Raises:
            MailError: サーバが OK を返さなかった場合
        """
        status, data = client.uid("FETCH", ",".join(uids), spec)
        if status != "OK":
            raise MailError(f"IMAP fetch failed: {status}")
        return parse_fetch_response(data)
