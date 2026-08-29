# tests/adapters/storage/test_ledger_storage.py
"""
LedgerStorageAdapter のテスト

Stage 2: 送信台帳の永続化（JSONL インデックス + sent/ 本文）
"""

import json
import logging
import os
import sys
from pathlib import Path

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
)

from adapters.storage.path_resolver import PathResolverAdapter
from domain.models import UNTRUSTED_EXTERNAL_DATA, ReplyRecord
from usecases.ports import LedgerPort

SENT_AT = "2026-08-28T21:05:00"
MSG_ID = "<176000000.1@example.com>"


def _read_lines(path: Path) -> list[str]:
    """JSONL の非空行を返す"""
    return [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]


class TestLedgerStorageAdapter:
    """LedgerStorageAdapter のテスト"""

    @pytest.fixture
    def path_resolver(self, tmp_path):
        """PathResolverAdapterを生成（実ホームには触れない）"""
        return PathResolverAdapter(base_dir=str(tmp_path))

    @pytest.fixture
    def adapter(self, path_resolver):
        """LedgerStorageAdapterを生成"""
        from adapters.storage.ledger_storage import LedgerStorageAdapter

        return LedgerStorageAdapter(path_resolver)

    @pytest.fixture
    def persistent_dir(self, path_resolver):
        """永続化ディレクトリ"""
        return Path(path_resolver.get_persistent_dir())

    def test_conforms_to_protocol(self, adapter):
        """Protocol準拠"""
        assert isinstance(adapter, LedgerPort)

    def test_load_records_empty_returns_empty_list(self, adapter):
        """台帳ファイルが存在しない場合は空リストを返す"""
        assert adapter.load_records() == []

    def test_record_sent_appends_line_and_writes_body(self, adapter, persistent_dir):
        """JSONL へ1行追記し、sent/ に本文ファイルを書く"""
        record = adapter.record_sent(
            message_id=MSG_ID,
            sent_at=SENT_AT,
            subject="日々の雑感: 静けさについて",
            recipient="reader@example.com",
            body="一行目\n\n二行目",
        )

        assert record is not None
        assert record.message_id == MSG_ID
        assert record.body_file == "sent/20260828_2105.md"

        ledger_file = persistent_dir / "essay_ledger.jsonl"
        assert len(_read_lines(ledger_file)) == 1

        body_file = persistent_dir / "sent" / "20260828_2105.md"
        assert body_file.exists()
        content = body_file.read_text(encoding="utf-8")
        assert content.startswith("---\n")
        assert '"日々の雑感: 静けさについて"' in content
        assert '"reader@example.com"' in content
        assert f'"{MSG_ID}"' in content
        assert content.endswith("一行目\n\n二行目\n")

    def test_record_sent_logs_completion_as_info(self, adapter, caplog):
        """記録完了が INFO 1 行として残る（DEBUG では閾値 INFO の下に沈む）"""
        with caplog.at_level(logging.INFO, logger="emailingessay"):
            record = adapter.record_sent(
                message_id=MSG_ID,
                sent_at=SENT_AT,
                subject="件名",
                recipient="reader@example.com",
                body="本文",
            )

        assert record is not None
        infos = [
            r
            for r in caplog.records
            if r.name.startswith("emailingessay") and r.levelno == logging.INFO
        ]
        assert len(infos) == 1
        assert record.body_file in infos[0].getMessage()

    def test_record_sent_roundtrips_through_load_records(self, adapter):
        """書いたレコードが load_records() で読み戻せる"""
        adapter.record_sent(
            message_id=MSG_ID,
            sent_at=SENT_AT,
            subject="日本語の件名",
            recipient="reader@example.com",
            body="本文",
        )

        loaded = adapter.load_records()
        assert len(loaded) == 1
        assert loaded[0].message_id == MSG_ID
        assert loaded[0].subject == "日本語の件名"
        assert loaded[0].sent_at == SENT_AT

    def test_load_records_skips_broken_lines(self, adapter, persistent_dir):
        """壊れた行は飛ばして残りを返す"""
        ledger_file = persistent_dir / "essay_ledger.jsonl"
        valid = {
            "message_id": MSG_ID,
            "sent_at": SENT_AT,
            "subject": "正常",
            "recipient": "reader@example.com",
            "body_file": "sent/20260828_2105.md",
        }
        lines = [
            json.dumps(valid, ensure_ascii=False),
            "{壊れた JSON",  # パース不能
            json.dumps({"message_id": "<x@example.com>"}, ensure_ascii=False),  # 欠落
            json.dumps(["リストであってdictでない"], ensure_ascii=False),
            "",  # 空行
        ]
        ledger_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        loaded = adapter.load_records()
        assert len(loaded) == 1
        assert loaded[0].subject == "正常"

    def test_record_sent_is_idempotent(self, adapter, persistent_dir):
        """同じ message_id で2回呼んでも台帳は1行のまま"""
        first = adapter.record_sent(
            message_id=MSG_ID,
            sent_at=SENT_AT,
            subject="一通目",
            recipient="reader@example.com",
            body="本文",
        )
        second = adapter.record_sent(
            message_id=MSG_ID,
            sent_at="2026-08-29T07:00:00",
            subject="重複",
            recipient="reader@example.com",
            body="別の本文",
        )

        assert first is not None
        assert second is None
        assert len(adapter.load_records()) == 1
        # 重複呼び出しは本文ファイルも残さない（副作用ゼロ）
        assert not (persistent_dir / "sent" / "20260829_0700.md").exists()

    def test_body_filename_collision_does_not_overwrite(self, adapter, persistent_dir):
        """同一分に2通送っても既存本文を上書きしない"""
        first = adapter.record_sent(
            message_id="<a@example.com>",
            sent_at=SENT_AT,
            subject="一通目",
            recipient="reader@example.com",
            body="一通目の本文",
        )
        second = adapter.record_sent(
            message_id="<b@example.com>",
            sent_at=SENT_AT,
            subject="二通目",
            recipient="reader@example.com",
            body="二通目の本文",
        )

        assert first is not None
        assert second is not None
        assert first.body_file == "sent/20260828_2105.md"
        assert second.body_file == "sent/20260828_2105_2.md"

        sent_dir = persistent_dir / "sent"
        assert "一通目の本文" in (sent_dir / "20260828_2105.md").read_text(
            encoding="utf-8"
        )
        assert "二通目の本文" in (sent_dir / "20260828_2105_2.md").read_text(
            encoding="utf-8"
        )
        assert len(adapter.load_records()) == 2

    def test_frontmatter_is_parseable_with_special_characters(
        self, adapter, persistent_dir
    ):
        """件名に : や " が含まれても frontmatter が壊れない"""
        subject = 'コロン: と "引用符" を含む件名'
        adapter.record_sent(
            message_id=MSG_ID,
            sent_at=SENT_AT,
            subject=subject,
            recipient="reader@example.com",
            body="本文",
        )

        content = (persistent_dir / "sent" / "20260828_2105.md").read_text(
            encoding="utf-8"
        )
        # frontmatter の値は JSON スカラ（YAML のダブルクォート形式と互換）
        header = content.split("---\n")[1]
        values = dict(
            line.split(": ", 1) for line in header.splitlines() if ": " in line
        )
        assert json.loads(values["subject"]) == subject
        assert json.loads(values["message_id"]) == MSG_ID


class TestLedgerStorageReplies:
    """返信側の永続化（Stage 4 の受け皿）"""

    @pytest.fixture
    def path_resolver(self, tmp_path):
        return PathResolverAdapter(base_dir=str(tmp_path))

    @pytest.fixture
    def adapter(self, path_resolver):
        from adapters.storage.ledger_storage import LedgerStorageAdapter

        return LedgerStorageAdapter(path_resolver)

    @pytest.fixture
    def reply(self):
        return ReplyRecord(
            message_id="<reply-1@example.com>",
            in_reply_to=MSG_ID,
            sender="reader@example.com",
            received_at="2026-08-29T08:00:00",
            body="返信の本文",
        )

    def test_load_replies_empty_returns_empty_list(self, adapter):
        """返信ファイルが存在しない場合は空リストを返す"""
        assert adapter.load_replies() == []

    def test_append_reply_and_load(self, adapter, path_resolver, reply):
        """返信を追記して読み戻せる"""
        assert adapter.append_reply(reply) is True

        replies_file = Path(path_resolver.get_persistent_dir()) / "essay_replies.jsonl"
        assert len(_read_lines(replies_file)) == 1

        loaded = adapter.load_replies()
        assert len(loaded) == 1
        assert loaded[0] == reply
        assert loaded[0].content_class == UNTRUSTED_EXTERNAL_DATA

    def test_append_reply_is_idempotent(self, adapter, reply):
        """同じ返信を二度取り込まない"""
        assert adapter.append_reply(reply) is True
        assert adapter.append_reply(reply) is False
        assert len(adapter.load_replies()) == 1

    def test_load_replies_skips_broken_lines(self, adapter, path_resolver, reply):
        """壊れた行は飛ばして残りを返す"""
        replies_file = Path(path_resolver.get_persistent_dir()) / "essay_replies.jsonl"
        lines = [
            json.dumps(reply.to_dict(), ensure_ascii=False),
            "{壊れた JSON",
            json.dumps({"message_id": "<x@example.com>"}, ensure_ascii=False),
        ]
        replies_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        loaded = adapter.load_replies()
        assert len(loaded) == 1
        assert loaded[0].message_id == reply.message_id
