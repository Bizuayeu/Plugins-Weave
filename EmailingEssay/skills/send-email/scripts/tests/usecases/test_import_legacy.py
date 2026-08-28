# tests/usecases/test_import_legacy.py
"""
遡及移行ユースケースのテスト（Stage 5）

移行対象はユーザーの記憶そのもの。件数だけでなく「どの本文にどの件名が
付いたか」を固定する（取り違えの検品）。
"""

import os
import sys
from datetime import datetime
from pathlib import Path

import pytest

# scriptsディレクトリをパスに追加
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from adapters.storage.ledger_storage import (
    LEDGER_FILE_NAME,
    SENT_DIR_NAME,
    LedgerStorageAdapter,
)
from adapters.storage.path_resolver import PathResolverAdapter
from usecases.import_legacy import ImportLegacyUseCase

RECIPIENT = "reader@example.com"


# =============================================================================
# フィクスチャ用ヘルパー
# =============================================================================


def write_file(directory: Path, name: str, content: str, when: str = "") -> Path:
    """UTF-8 でファイルを作り、必要なら mtime を固定する"""
    path = directory / name
    path.write_text(content, encoding="utf-8", newline="\n")
    if when:
        stamp = datetime.fromisoformat(when).timestamp()
        os.utime(path, (stamp, stamp))
    return path


def wait_log_line(timestamp: str, subject: str, to: str = RECIPIENT) -> str:
    """essay_wait.log の SENT 行を組み立てる（実データと同じ書式）"""
    return f"[{timestamp}] non-interactive essay SENT to {to} | subject={subject}\n"


@pytest.fixture
def usecase_factory(tmp_path):
    """移行元 = 台帳の置き場（実データと同じ配置）でユースケースを組む"""

    def build() -> ImportLegacyUseCase:
        ledger = LedgerStorageAdapter(PathResolverAdapter(base_dir=str(tmp_path)))
        return ImportLegacyUseCase(
            source_dir=str(tmp_path), ledger=ledger, recipient=RECIPIENT
        )

    return build


# =============================================================================
# 件名の復元
# =============================================================================


class TestSubjectRestoration:
    """件名復元の 2 経路（推定経路は持たない）"""

    def test_subject_file_wins_over_wait_log(self, tmp_path, usecase_factory):
        """① 件名ファイルがあればそれを使う（② より優先）"""
        write_file(tmp_path, "essay_body_20260816.txt", "本文", "2026-08-16 21:06:00")
        write_file(
            tmp_path,
            "essay_subject_20260816.txt",
            "件名ファイル側の件名\n",
            "2026-08-16 21:06:00",
        )
        write_file(
            tmp_path,
            "essay_wait.log",
            wait_log_line("2026-08-16 21:07:00", "ログ側の件名"),
        )

        plan = usecase_factory().plan()

        assert [i.body_file for i in plan.items] == ["essay_body_20260816.txt"]
        item = plan.items[0]
        assert item.subject == "件名ファイル側の件名"
        assert item.subject_source.startswith("subject-file:")
        # 送信時刻の出所はログ側が確か（件名の優先順位とは別）
        assert item.sent_at == "2026-08-16T21:07:00"

    def test_falls_back_to_wait_log(self, tmp_path, usecase_factory):
        """② 件名ファイルが無ければ SENT 行から復元する"""
        write_file(tmp_path, "_essay_body_20260721.txt", "本文", "2026-07-21 21:25:00")
        write_file(
            tmp_path,
            "essay_wait.log",
            wait_log_line("2026-07-21 21:26:05", "日々の雑感 — 定理の立たない日に"),
        )

        plan = usecase_factory().plan()

        assert len(plan.items) == 1
        item = plan.items[0]
        assert item.body_file == "_essay_body_20260721.txt"
        assert item.subject == "日々の雑感 — 定理の立たない日に"
        assert item.subject_source.startswith("wait-log:")
        assert item.sent_at == "2026-07-21T21:26:05"
        assert item.recipient == RECIPIENT

    def test_body_without_any_source_is_excluded(self, tmp_path, usecase_factory):
        """両方欠けた本文は除外側に落ちる（1 行目やファイル名から推定しない）"""
        write_file(tmp_path, "_essay_body_20260603.txt", "推定できる 1 行目\n本文")

        plan = usecase_factory().plan()

        assert plan.items == ()
        assert [s.body_file for s in plan.skipped] == ["_essay_body_20260603.txt"]
        assert "件名" in plan.skipped[0].reason

    def test_picks_the_later_body_on_a_two_essay_day(self, tmp_path, usecase_factory):
        """同日 2 本の本文があり SENT 行が 1 行なら、その時刻の直前の本文を採る

        実データ 2026-07-16（朝の本編と _pm）の形。ここを取り違えても件数は
        17 のまま変わらないため、テストで固定する。
        """
        write_file(
            tmp_path, "_essay_body_20260716.txt", "朝の本文", "2026-07-16 07:52:00"
        )
        write_file(
            tmp_path, "_essay_body_20260716_pm.txt", "夜の本文", "2026-07-16 21:08:00"
        )
        write_file(
            tmp_path,
            "essay_wait.log",
            wait_log_line("2026-07-16 21:09:05", "夜に送った件名"),
        )

        plan = usecase_factory().plan()

        assert [i.body_file for i in plan.items] == ["_essay_body_20260716_pm.txt"]
        assert [s.body_file for s in plan.skipped] == ["_essay_body_20260716.txt"]

    def test_subject_file_matches_body_by_suffix(self, tmp_path, usecase_factory):
        """件名ファイルと本文は同日 2 通目のサフィックスまで含めて対応する"""
        write_file(
            tmp_path, "essay_body_20260814.txt", "朝の本文", "2026-08-14 01:06:00"
        )
        write_file(
            tmp_path, "essay_body_20260814_pm.txt", "夜の本文", "2026-08-14 21:07:00"
        )
        write_file(
            tmp_path,
            "essay_subject_20260814_pm.txt",
            "夜の件名\n",
            "2026-08-14 21:07:00",
        )

        plan = usecase_factory().plan()

        assert [i.body_file for i in plan.items] == ["essay_body_20260814_pm.txt"]
        assert plan.items[0].subject == "夜の件名"
        assert plan.items[0].sent_at == "2026-08-14T21:07:00"

    def test_undated_subject_file_is_not_used(self, tmp_path, usecase_factory):
        """日付を持たない件名ファイル（essay_subject.txt）は突合の鍵にならない"""
        write_file(tmp_path, "essay_body.txt", "本文", "2026-08-17 21:06:00")
        write_file(tmp_path, "essay_subject.txt", "宛先不明の件名\n")

        plan = usecase_factory().plan()

        assert plan.items == ()
        assert [s.body_file for s in plan.skipped] == ["essay_body.txt"]


# =============================================================================
# 作業ゴミと突合の異常
# =============================================================================


class TestJunkAndDiscrepancies:
    """作業ゴミの除外と、黙って進まない性質"""

    @pytest.mark.parametrize(
        "name",
        [
            "temp_essay_body.txt",
            "_tmp_essay_body.txt",
            "essay_body_tmp.txt",
            "essay_body_temp.txt",
            "essay_body_latest.txt",
        ],
    )
    def test_junk_is_excluded_even_when_a_sent_line_fits(
        self, tmp_path, usecase_factory, name
    ):
        """作業ゴミは SENT 行の直前に書かれていても本編と取り違えない"""
        write_file(tmp_path, name, "作業ゴミ", "2026-07-23 21:09:00")
        write_file(
            tmp_path, "essay_wait.log", wait_log_line("2026-07-23 21:10:00", "件名")
        )

        plan = usecase_factory().plan()

        assert plan.items == ()
        assert [s.body_file for s in plan.skipped] == [name]
        assert plan.skipped[0].reason == "作業ゴミ"
        assert plan.warnings  # 対応する本文の無い SENT 行として報告される

    def test_sent_line_without_a_body_is_reported(self, tmp_path, usecase_factory):
        """本文の見つからない SENT 行は警告として出す（黙って落とさない）"""
        write_file(tmp_path, "_essay_body_20260702.txt", "本文", "2026-07-02 06:46:00")
        write_file(
            tmp_path,
            "essay_wait.log",
            wait_log_line("2026-07-02 06:47:19", "拾える件名")
            + wait_log_line("2026-07-05 21:00:00", "本文の無い件名"),
        )

        plan = usecase_factory().plan()

        assert len(plan.items) == 1
        assert any("本文の無い件名" in w for w in plan.warnings)

    def test_one_body_is_claimed_by_one_sent_line(self, tmp_path, usecase_factory):
        """1 本の本文を 2 行の SENT 行が取り合わない"""
        write_file(tmp_path, "_essay_body_20260702.txt", "本文", "2026-07-02 06:46:00")
        write_file(
            tmp_path,
            "essay_wait.log",
            wait_log_line("2026-07-02 06:47:19", "一通目")
            + wait_log_line("2026-07-02 21:06:00", "二通目"),
        )

        plan = usecase_factory().plan()

        assert [i.subject for i in plan.items] == ["一通目"]
        assert any("二通目" in w for w in plan.warnings)

    def test_conflicting_subjects_are_reported(self, tmp_path, usecase_factory):
        """2 経路の件名が食い違えば警告する（片方を黙って採らない）"""
        write_file(tmp_path, "_essay_body_20260730.txt", "本文", "2026-07-30 21:40:00")
        write_file(tmp_path, "_essay_subject_20260730.txt", "件名 A\n")
        write_file(
            tmp_path, "essay_wait.log", wait_log_line("2026-07-30 21:40:18", "件名 B")
        )

        plan = usecase_factory().plan()

        assert plan.items[0].subject == "件名 A"
        assert any("_essay_body_20260730.txt" in w for w in plan.warnings)

    def test_broken_bytes_in_wait_log_do_not_kill_the_run(
        self, tmp_path, usecase_factory
    ):
        """読めないバイトが混じっても全体が落ちない（cp932 事故対策）"""
        write_file(tmp_path, "_essay_body_20260721.txt", "本文", "2026-07-21 21:25:00")
        log = tmp_path / "essay_wait.log"
        log.write_bytes(
            b"[2026-07-20 21:00:00] \x93\xfa broken line\n"
            + wait_log_line("2026-07-21 21:26:05", "拾える件名").encode("utf-8")
        )

        plan = usecase_factory().plan()

        assert [i.subject for i in plan.items] == ["拾える件名"]

    def test_missing_wait_log_is_not_an_error(self, tmp_path, usecase_factory):
        """ログが無くても件名ファイル経路だけで走る"""
        write_file(tmp_path, "essay_body_20260815.txt", "本文", "2026-08-15 21:10:00")
        write_file(tmp_path, "essay_subject_20260815.txt", "件名\n")

        plan = usecase_factory().plan()

        assert [i.subject for i in plan.items] == ["件名"]


# =============================================================================
# dry-run と実行
# =============================================================================


class TestDryRunAndExecute:
    """dry-run は何も書かない。実行は追記のみで、二度目は増えない"""

    def test_plan_writes_nothing(self, tmp_path, usecase_factory):
        """plan() 実行後、台帳ファイルも sent/ も生成されない"""
        write_file(tmp_path, "_essay_body_20260721.txt", "本文", "2026-07-21 21:25:00")
        write_file(
            tmp_path, "essay_wait.log", wait_log_line("2026-07-21 21:26:05", "件名")
        )
        before = sorted(p.name for p in tmp_path.iterdir())

        plan = usecase_factory().plan()

        assert len(plan.items) == 1
        assert sorted(p.name for p in tmp_path.iterdir()) == before
        assert not (tmp_path / LEDGER_FILE_NAME).exists()
        assert not (tmp_path / SENT_DIR_NAME).exists()

    def test_execute_appends_records(self, tmp_path, usecase_factory):
        """実行すると台帳 1 行と本文 1 ファイルができ、本文が読み戻せる"""
        write_file(
            tmp_path, "_essay_body_20260721.txt", "本文の中身\n", "2026-07-21 21:25:00"
        )
        write_file(
            tmp_path, "essay_wait.log", wait_log_line("2026-07-21 21:26:05", "件名")
        )

        records = usecase_factory().execute()

        assert len(records) == 1
        lines = (tmp_path / LEDGER_FILE_NAME).read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        body_path = tmp_path / records[0].body_file
        assert "本文の中身" in body_path.read_text(encoding="utf-8")
        assert records[0].subject == "件名"

    def test_execute_leaves_source_files_untouched(self, tmp_path, usecase_factory):
        """移行元は読むだけ（削除も改変もしない）"""
        source = write_file(
            tmp_path, "_essay_body_20260721.txt", "本文", "2026-07-21 21:25:00"
        )
        write_file(
            tmp_path, "essay_wait.log", wait_log_line("2026-07-21 21:26:05", "件名")
        )
        before = source.read_bytes()

        usecase_factory().execute()

        assert source.exists()
        assert source.read_bytes() == before

    def test_execute_is_idempotent(self, tmp_path, usecase_factory):
        """2 回実行しても台帳が二重にならない"""
        write_file(tmp_path, "_essay_body_20260721.txt", "本文", "2026-07-21 21:25:00")
        write_file(
            tmp_path, "essay_wait.log", wait_log_line("2026-07-21 21:26:05", "件名")
        )

        first = usecase_factory().execute()
        second = usecase_factory().execute()

        assert len(first) == 1
        assert second == []
        lines = (tmp_path / LEDGER_FILE_NAME).read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert len(list((tmp_path / SENT_DIR_NAME).iterdir())) == 1

    def test_message_id_marks_the_record_as_migrated(self, tmp_path, usecase_factory):
        """移行分の message_id は移行分と分かる形（かつ本文ごとに決まる）"""
        write_file(tmp_path, "_essay_body_20260721.txt", "本文", "2026-07-21 21:25:00")
        write_file(
            tmp_path, "essay_wait.log", wait_log_line("2026-07-21 21:26:05", "件名")
        )

        message_id = usecase_factory().plan().items[0].message_id

        assert message_id.startswith("<legacy.")
        assert message_id.endswith(">")
        assert "_essay_body_20260721" in message_id
