# adapters/storage/ledger_storage.py
"""
送信台帳ストレージアダプター

送信したエッセイを追記専用の JSONL（索引）と sent/ 配下の本文ファイルへ
永続化する。返信の取り込み結果も同じ形式で別ファイルに保持する。

索引と実体を分けるのは、1 年分の本文を 1 ファイルに抱えると
「索引だけ安く読む」用途が壊れるため（IMPLEMENTATION_PLAN Decision 3）。

Stage 2: 台帳の永続化
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from domain.models import LedgerRecord
from domain.validators import validate_ledger_records, validate_reply_records
from frameworks.logging_config import get_logger

if TYPE_CHECKING:
    from domain.models import ReplyRecord
    from usecases.ports import PathResolverPort

LEDGER_FILE_NAME = "essay_ledger.jsonl"
REPLIES_FILE_NAME = "essay_replies.jsonl"
SENT_DIR_NAME = "sent"

# frontmatter に出す台帳フィールド（本文ファイル単体でも出所が辿れるように）
_FRONTMATTER_FIELDS = ("message_id", "sent_at", "subject", "recipient")
_FRONTMATTER_DELIMITER = "---"

# モジュールロガー
logger = get_logger("storage")


def _strip_frontmatter(text: str) -> str:
    """
    `_write_body` が付けた先頭の frontmatter を落とす。

    区切りは行単位で見る——件名に含まれる `---` は json.dumps された値の内側に
    あり、行全体が区切りに化けることはない。閉じが無ければ frontmatter ではない
    と見なし、本文をそのまま返す。

    Args:
        text: 本文ファイルの中身

    Returns:
        frontmatter を除いた本文
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_DELIMITER:
        return text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == _FRONTMATTER_DELIMITER:
            return "\n".join(lines[index + 1 :])
    return text


class LedgerStorageAdapter:
    """
    送信台帳ストレージアダプター（LedgerPort実装）

    追記専用。既存行の書き換えも削除も行わない。
    """

    def __init__(self, path_resolver: PathResolverPort) -> None:
        """
        Args:
            path_resolver: パス解決アダプター
        """
        self._path_resolver = path_resolver

    # -------------------------------------------------------------------------
    # パス解決
    # -------------------------------------------------------------------------

    def _get_ledger_file(self) -> Path:
        """台帳ファイルのパスを取得"""
        return Path(self._path_resolver.get_persistent_dir()) / LEDGER_FILE_NAME

    def _get_replies_file(self) -> Path:
        """返信ファイルのパスを取得"""
        return Path(self._path_resolver.get_persistent_dir()) / REPLIES_FILE_NAME

    def _sent_dir_path(self) -> Path:
        """本文ディレクトリのパス（作らない——読み取り経路に副作用を持たせない）"""
        return Path(self._path_resolver.get_persistent_dir()) / SENT_DIR_NAME

    def _get_sent_dir(self) -> Path:
        """本文ディレクトリのパスを取得（なければ作成）"""
        sent_dir = self._sent_dir_path()
        sent_dir.mkdir(parents=True, exist_ok=True)
        return sent_dir

    # -------------------------------------------------------------------------
    # JSONL の読み書き
    # -------------------------------------------------------------------------

    def _read_jsonl(self, filepath: Path) -> list[Any]:
        """
        JSONL を 1 行ずつパースする。

        壊れた行は飛ばす（1 行の破損で全損させないための JSONL 採用）。

        Args:
            filepath: 読み込むファイルパス

        Returns:
            パースできた値のリスト（型検証は呼び出し側の validator が行う）
        """
        if not filepath.exists():
            return []

        records: list[Any] = []
        try:
            with filepath.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Skipped corrupted line in {filepath.name}")
        except OSError as e:
            logger.warning(f"Failed to read {filepath.name}: {e}")
            return []
        return records

    def _append_jsonl(self, filepath: Path, payload: dict[str, Any]) -> None:
        """
        JSONL へ 1 行追記する。

        改行は明示的に "\\n" 固定。grep / jq で読む追記専用ファイルであり、
        プラットフォーム依存の改行変換を挟まない。

        Args:
            filepath: 追記先のファイルパス
            payload: 追記する辞書
        """
        line = json.dumps(payload, ensure_ascii=False)
        with filepath.open("a", encoding="utf-8", newline="\n") as f:
            f.write(line + "\n")

    # -------------------------------------------------------------------------
    # 送信の記録
    # -------------------------------------------------------------------------

    def _body_path(self, sent_at: str) -> Path:
        """
        本文ファイルのパスを決める。

        既存ファイルがあれば _2, _3, ... と採番し、既存本文を上書きしない
        （同一分に 2 通送った場合）。

        Args:
            sent_at: ISO 8601 形式の送信日時

        Returns:
            まだ存在しない本文ファイルのパス

        Raises:
            ValueError: sent_at が ISO 8601 として解釈できない場合
        """
        stem = datetime.fromisoformat(sent_at).strftime("%Y%m%d_%H%M")
        sent_dir = self._get_sent_dir()

        candidate = sent_dir / f"{stem}.md"
        suffix = 1
        while candidate.exists():
            suffix += 1
            candidate = sent_dir / f"{stem}_{suffix}.md"
        return candidate

    def _write_body(self, filepath: Path, record: LedgerRecord, body: str) -> None:
        """
        YAML frontmatter 付きで本文を書き出す。

        frontmatter の値は json.dumps で出す。YAML のダブルクォート形式と
        互換で、件名の : や " や日本語をエスケープ規則ごと任せられる。

        Args:
            filepath: 書き出し先
            record: 台帳レコード（frontmatter の出所）
            body: 本文
        """
        values = record.to_dict()
        lines = [_FRONTMATTER_DELIMITER]
        lines += [
            f"{key}: {json.dumps(values[key], ensure_ascii=False)}"
            for key in _FRONTMATTER_FIELDS
        ]
        lines += [_FRONTMATTER_DELIMITER, ""]
        content = "\n".join(lines) + "\n" + body.rstrip("\n") + "\n"

        with filepath.open("w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    def record_sent(
        self,
        message_id: str,
        sent_at: str,
        subject: str,
        recipient: str,
        body: str,
    ) -> LedgerRecord | None:
        """
        送信を台帳に記録する。

        同じ message_id が既にある場合は何も書かずに None を返す（冪等）。
        重複判定を本文の書き出しより先に行うため、孤児ファイルは残らない。

        Args:
            message_id: 採番済み Message-ID（角括弧込み）
            sent_at: ISO 8601 形式の送信日時
            subject: 送信した件名
            recipient: 宛先アドレス
            body: 本文

        Returns:
            記録した LedgerRecord。既出の場合は None
        """
        if any(r.message_id == message_id for r in self.load_records()):
            logger.debug(f"Ledger already has message_id: {message_id}")
            return None

        body_path = self._body_path(sent_at)
        record = LedgerRecord(
            message_id=message_id,
            sent_at=sent_at,
            subject=subject,
            recipient=recipient,
            body_file=f"{SENT_DIR_NAME}/{body_path.name}",
        )

        self._write_body(body_path, record, body)
        self._append_jsonl(self._get_ledger_file(), record.to_dict())
        logger.debug(f"Recorded to ledger: {record.body_file}")
        return record

    def load_records(self) -> list[LedgerRecord]:
        """
        台帳を読み込む。

        Returns:
            有効な LedgerRecord のリスト（壊れた行は除外）
        """
        return validate_ledger_records(self._read_jsonl(self._get_ledger_file()))

    def load_sent_bodies(self) -> list[str]:
        """
        記録済みの本文を frontmatter 抜きで読み出す。

        frontmatter を付けた `_write_body` と対になるよう、剥がすのもここに置く。
        1 ファイルが読めないだけで全体を落とさない（JSONL の壊れた行と同じ扱い）。

        Returns:
            記録済み本文のリスト（読めないファイルは除外）
        """
        bodies: list[str] = []
        for path in sorted(self._sent_dir_path().glob("*.md")):
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError) as e:
                logger.warning(f"Failed to read {path.name}: {e}")
                continue
            bodies.append(_strip_frontmatter(text))
        return bodies

    # -------------------------------------------------------------------------
    # 返信の記録
    # -------------------------------------------------------------------------

    def append_reply(self, reply: ReplyRecord) -> bool:
        """
        取り込んだ返信を追記する。

        Args:
            reply: 返信レコード

        Returns:
            追記した場合は True。message_id が既出の場合は False（冪等）
        """
        if any(r.message_id == reply.message_id for r in self.load_replies()):
            logger.debug(f"Replies already has message_id: {reply.message_id}")
            return False

        self._append_jsonl(self._get_replies_file(), reply.to_dict())
        return True

    def load_replies(self) -> list[ReplyRecord]:
        """
        返信一覧を読み込む。

        Returns:
            有効な ReplyRecord のリスト（壊れた行は除外）
        """
        return validate_reply_records(self._read_jsonl(self._get_replies_file()))
