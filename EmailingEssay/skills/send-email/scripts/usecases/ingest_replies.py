# usecases/ingest_replies.py
"""
返信取り込みユースケース

台帳の Message-ID を鍵に、返ってきた返信だけを取り込む。
受信箱を横断検索はしない——自分が投げた球の跳ね返りだけを拾う（攻撃面の最小化）。

取り込んだ本文は外部入力であり、ReplyRecord.content_class がその素性を表明する
（ops-rules 7 のフェンシング）。判定はここで行い、受信箱の実装（IMAP か否か）
には依存しない。

Stage 4: IMAP による返信の取り込み
"""

from __future__ import annotations

import re
from email.utils import parseaddr
from typing import TYPE_CHECKING

from frameworks.logging_config import get_logger

if TYPE_CHECKING:
    from domain.models import ReplyRecord

    from .ports import InboxPort, LedgerPort

logger = get_logger("replies")

__all__ = [
    "GMAIL_AUTHSERV_ID",
    "IngestRepliesUseCase",
    "normalize_message_id",
    "parse_auth_results",
]

# 根拠として認める authserv-id。Authentication-Results は誰でも自分で書けるので、
# 受信側 MTA が自分の名前で付けた 1 本だけを証拠に採る（受信は Gmail 固定）。
GMAIL_AUTHSERV_ID = "mx.google.com"

# 通過に必要な method。dkim と spf がともに pass のときだけ通す
_REQUIRED_AUTH_METHODS = ("dkim", "spf")
_AUTH_PASS = "pass"

# 同じ method が食い違う結果で二度現れたときに入れる印。RFC 8601 の結果値に
# 無い語を使い、どちらの結果にも倒さない（＝pass 側に倒さない）。
_CONFLICTING_RESULT = "conflict"

# method[/version] = result。result は空白区切りの 1 トークンとして完全一致で
# 読む（前方一致にすると dkim=passfail が pass として通る）。
_AUTH_METHOD_RE = re.compile(r"([A-Za-z][A-Za-z0-9-]*)\s*(?:/\s*\d+\s*)?=\s*(\S+)")


def normalize_message_id(value: str) -> str:
    """
    Message-ID を突合可能な形へ正規化する。

    ヘッダの折り返し（CRLF + 空白）と角括弧の有無は経路によって揺れるため、
    空白を全て除いてから角括弧を外した形で比較する。

    Args:
        value: 生の Message-ID / In-Reply-To 値

    Returns:
        正規化された識別子
    """
    return "".join(value.split()).strip("<>")


def _strip_comments(value: str) -> str:
    """
    RFC 5322 のコメント（括弧）を空白 1 つに畳む。

    コメント内のセミコロンは method の区切りではないため、分解の前に落とす
    必要がある——落とさないと、コメントに紛れ込ませた `; dkim=pass` が
    本物の `dkim=fail` を上書きできてしまう。引用符の中の括弧はコメントを
    開閉しないものとして扱う（閉じ括弧を引用符で隠してコメントを早く終わらせ、
    残りを本物の method として読ませる手を塞ぐ）。

    Args:
        value: Authentication-Results ヘッダの値

    Returns:
        コメントを除いた文字列
    """
    out: list[str] = []
    depth = 0  # コメントの入れ子の深さ（0 なら本文）
    quoted = False
    escaped = False

    for char in value:
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif quoted:
            quoted = char != '"'
        elif char == '"':
            quoted = True
        elif char == "(":
            depth += 1
            continue
        # 対応する開き括弧を持つ ")" だけがコメントを閉じる。宙に浮いた ")" を
        # 落とすと `dkim=pass)` が `pass` に化けるため、素の文字として残す。
        elif char == ")" and depth:
            depth -= 1
            out.append(" ")  # コメントは折り返し空白と同じ扱い（語を繋げない）
            continue

        if depth == 0:
            out.append(char)

    return "".join(out)


def parse_auth_results(value: str) -> tuple[str, dict[str, str]]:
    """
    Authentication-Results ヘッダを authserv-id と method 別の結果に分解する。

    authserv-id は「誰が検証したか」であり、これが受信側 MTA の名前でなければ
    結果は根拠にならない（送信者が自分で書けるため）。結果は casefold して返す。
    同じ method が食い違う結果で二度現れた場合は、どちらにも倒さず印を入れる。

    Args:
        value: Authentication-Results ヘッダの値（不在なら空文字）

    Returns:
        (authserv-id, {method: result}) の組。読めなければ ("", {})
    """
    sections = _strip_comments(value).split(";")

    head = sections[0].split()
    authserv_id = head[0].casefold() if head else ""

    results: dict[str, str] = {}
    for section in sections[1:]:
        match = _AUTH_METHOD_RE.match(section.strip())
        if match is None:
            continue
        method, result = match.group(1).casefold(), match.group(2).casefold()
        if method in results and results[method] != result:
            results[method] = _CONFLICTING_RESULT
            continue
        results[method] = result

    return authserv_id, results


def _is_verified_by_receiving_mta(auth_results: str) -> bool:
    """
    受信側 MTA の検証結果として差出人が確かめられているか判定する。

    Args:
        auth_results: Authentication-Results ヘッダの値

    Returns:
        authserv-id が受信側 MTA のもので、dkim / spf がともに pass なら True
        （ヘッダ不在・別名義・1 つでも pass でなければ False ＝ fail-closed）
    """
    authserv_id, results = parse_auth_results(auth_results)
    if authserv_id != GMAIL_AUTHSERV_ID:
        return False
    return all(results.get(m) == _AUTH_PASS for m in _REQUIRED_AUTH_METHODS)


def _one_line(value: str) -> str:
    """ログに載せる外部値を 1 行に畳む（改行でログ行を割らせない）。"""
    return " ".join(value.split())


class IngestRepliesUseCase:
    """返信取り込みユースケース"""

    def __init__(self, inbox: InboxPort, ledger: LedgerPort, recipient: str) -> None:
        """
        Args:
            inbox: InboxPort 実装
            ledger: LedgerPort 実装（台帳と返信の永続化）
            recipient: 送信先アドレス（返信の差出人として唯一許可する相手）
        """
        self._inbox = inbox
        self._ledger = ledger
        self._recipient = recipient

    def fetch(self) -> list[ReplyRecord]:
        """
        受信箱から返信を取り込む。

        取り込むのは「In-Reply-To が台帳の message_id と一致」かつ
        「From が送信先と一致」する返信のみ。冪等性は LedgerPort が
        返信自身の Message-ID で担保する。

        Returns:
            今回新たに追記された返信のリスト

        Raises:
            MailError: 受信箱への接続・認証・取得に失敗した場合
        """
        sent_ids = {
            normalize_message_id(r.message_id) for r in self._ledger.load_records()
        }

        ingested: list[ReplyRecord] = []
        for candidate in self._inbox.fetch_replies(self._recipient):
            if not self._is_accepted(candidate, sent_ids):
                continue
            if self._ledger.append_reply(candidate):
                ingested.append(candidate)

        logger.info(f"Ingested replies: {len(ingested)}")
        return ingested

    def _is_accepted(self, candidate: ReplyRecord, sent_ids: set[str]) -> bool:
        """
        取り込み判定。

        4 つの関門（Message-ID / In-Reply-To / From / Authentication-Results）を
        全て通ったものだけを取り込む。落とした候補は理由を 1 行残す——返信は
        台帳の送信数に対して稀にしか来ず、転送・メーリングリスト・ISP の
        書き換えで認証が落ちた正当な返信が痕跡ゼロで消えると気付けないため。
        本文はログに出さない（外部入力を素で流す経路を作らない）。

        Args:
            candidate: 受信箱から得た返信候補
            sent_ids: 台帳にある送信済み Message-ID（正規化済み）

        Returns:
            取り込む場合は True
        """
        message_id = _one_line(candidate.message_id)
        sender = _one_line(candidate.sender)
        origin = f"message_id={message_id}, from={sender}"

        if not normalize_message_id(candidate.message_id):
            # 冪等性の鍵が立たない候補は取り込まない
            logger.info(f"Dropped a reply candidate: no Message-ID (from={sender})")
            return False

        if normalize_message_id(candidate.in_reply_to) not in sent_ids:
            logger.info(
                f"Dropped a reply candidate: In-Reply-To matches no sent essay ({origin})"
            )
            return False

        address = parseaddr(candidate.sender)[1].casefold()
        if not address or address != self._recipient.casefold():
            logger.info(
                f"Dropped a reply candidate: From is not the essay recipient ({origin})"
            )
            return False

        if not _is_verified_by_receiving_mta(candidate.auth_results):
            logger.info(
                f"Dropped a reply candidate: Authentication-Results did not "
                f"verify the sender ({origin})"
            )
            return False

        return True
