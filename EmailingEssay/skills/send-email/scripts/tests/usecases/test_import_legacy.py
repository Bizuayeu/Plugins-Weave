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
from usecases.import_legacy import RECORDED_BODY_REASON, ImportLegacyUseCase

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


# =============================================================================
# ランナーからの復元（③）
# =============================================================================

# 実物の形を写したランナー（`send_essay_20260827_2112.py` 世代）
LITERAL_RUNNER = '''# -*- coding: utf-8 -*-
"""EmailingEssay 送信ランナー Windows cp932 回避版"""

import sys
from pathlib import Path

SCRIPTS_DIR = r"C:\\Users\\anyth\\.claude\\plugins\\marketplaces\\plugins-weave"
BODY_PATH = Path(r"C:\\Users\\anyth\\.claude\\plugins\\.emailingessay\\{body}")

SUBJECT = "{subject}"


def main() -> int:
    body = BODY_PATH.read_text(encoding="utf-8-sig").strip()

    from usecases.factories import get_mail_adapter

    get_mail_adapter().send_custom(SUBJECT, body)
    return 0
'''

# 実物の形を写したランナー（`_send_20260611.py` 世代）
OLD_LITERAL_RUNNER = """# -*- coding: utf-8 -*-
import sys
from pathlib import Path

body_path = Path(r"C:\\Users\\anyth\\.claude\\plugins\\.emailingessay\\{body}")
content = body_path.read_text(encoding="utf-8").strip("\\n")

subject = "{subject}"

adapter.send_custom(subject=subject, content=content)
"""

# 実物の形を写したランナー（`_send_20260724.py` 世代——件名もファイルから読む）
FILE_SUBJECT_RUNNER = """# -*- coding: utf-8 -*-
import sys
from pathlib import Path

DATA = r"C:\\Users\\anyth\\.claude\\plugins\\.emailingessay"

subject = Path(DATA, "{subject_file}").read_text(encoding="utf-8").strip()
body = Path(DATA, "{body}").read_text(encoding="utf-8").strip("\\n")
"""


def write_runner(
    directory: Path, name: str, source: str, encoding: str = "utf-8"
) -> Path:
    """送信ランナーを置く（encoding は移行元の世代差を再現するため）"""
    path = directory / name
    path.write_bytes(source.encode(encoding))
    return path


class TestRunnerRestoration:
    """③ 送信ランナー内の plain な件名リテラルから復元する"""

    def test_restores_from_a_dated_runner(self, tmp_path, usecase_factory):
        """① ② が無くても、日付付きランナーの件名リテラルで復元する"""
        write_file(
            tmp_path, "essay_body_20260827_2112.txt", "本文", "2026-08-27 21:12:00"
        )
        write_runner(
            tmp_path,
            "send_essay_20260827_2112.py",
            LITERAL_RUNNER.format(
                body="essay_body_20260827_2112.txt",
                subject="意図は見えないが、意図が見えなくなる書き方は見える",
            ),
        )

        plan = usecase_factory().plan()

        assert [i.body_file for i in plan.items] == ["essay_body_20260827_2112.txt"]
        item = plan.items[0]
        assert item.subject == "意図は見えないが、意図が見えなくなる書き方は見える"
        assert item.subject_source == "runner:send_essay_20260827_2112.py"
        # ③ 単独なら送信時刻は本文の mtime、宛先は既定値（ランナー名から推測しない）
        assert item.sent_at == "2026-08-27T21:12:00"
        assert item.recipient == RECIPIENT
        assert plan.warnings == ()

    def test_restores_from_the_old_generation_runner(self, tmp_path, usecase_factory):
        """③ 旧世代（`subject = "..."` を後ろに置く形）でも同じく復元する"""
        write_file(tmp_path, "_essay_body_20260611.txt", "本文", "2026-06-11 21:18:00")
        write_runner(
            tmp_path,
            "_send_20260611.py",
            OLD_LITERAL_RUNNER.format(
                body="_essay_body_20260611.txt",
                subject="日々の雑感 — 認知の所在",
            ),
        )

        plan = usecase_factory().plan()

        assert [i.subject for i in plan.items] == ["日々の雑感 — 認知の所在"]
        assert plan.items[0].subject_source == "runner:_send_20260611.py"

    def test_subject_file_wins_over_runner(self, tmp_path, usecase_factory):
        """① 件名ファイルがあれば ③ は使わない（③ は ① ② を上回らない）"""
        write_file(tmp_path, "essay_body_20260815.txt", "本文", "2026-08-15 21:10:00")
        write_file(tmp_path, "essay_subject_20260815.txt", "件名ファイル側の件名\n")
        write_runner(
            tmp_path,
            "send_20260815.py",
            LITERAL_RUNNER.format(
                body="essay_body_20260815.txt", subject="ランナー側の件名"
            ),
        )

        plan = usecase_factory().plan()

        assert [i.subject for i in plan.items] == ["件名ファイル側の件名"]
        assert plan.items[0].subject_source.startswith("subject-file:")

    def test_wait_log_wins_over_runner(self, tmp_path, usecase_factory):
        """② SENT 行があれば ③ は使わない"""
        write_file(tmp_path, "_essay_body_20260703.txt", "本文", "2026-07-04 00:05:00")
        write_file(
            tmp_path,
            "essay_wait.log",
            wait_log_line("2026-07-04 00:05:30", "ログ側の件名"),
        )
        write_runner(
            tmp_path,
            "_send_20260703.py",
            OLD_LITERAL_RUNNER.format(
                body="_essay_body_20260703.txt", subject="ランナー側の件名"
            ),
        )

        plan = usecase_factory().plan()

        assert [i.subject for i in plan.items] == ["ログ側の件名"]
        assert plan.items[0].subject_source.startswith("wait-log:")

    def test_file_reference_subject_is_not_taken(self, tmp_path, usecase_factory):
        """件名をファイルから読むランナーは採らない（送った値がソースに無い）"""
        write_file(tmp_path, "_essay_body_20260724.txt", "本文", "2026-07-24 21:19:00")
        write_runner(
            tmp_path,
            "_send_20260724.py",
            FILE_SUBJECT_RUNNER.format(
                subject_file="_essay_subject_20260724.txt",
                body="_essay_body_20260724.txt",
            ),
        )

        plan = usecase_factory().plan()

        assert plan.items == ()
        assert [s.body_file for s in plan.skipped] == ["_essay_body_20260724.txt"]
        assert any("_send_20260724.py" in w for w in plan.warnings)

    def test_cp932_runner_is_decoded(self, tmp_path, usecase_factory):
        """cp932 で書かれたランナーからも件名が化けずに復元する"""
        write_file(tmp_path, "essay_body_20260804.txt", "本文", "2026-08-04 21:06:00")
        write_runner(
            tmp_path,
            "_send_20260804.py",
            OLD_LITERAL_RUNNER.format(
                body="essay_body_20260804.txt",
                subject="【日々の雑感】慎みは、いつから一滴ずつになったか",
            ),
            encoding="cp932",
        )

        plan = usecase_factory().plan()

        assert [i.subject for i in plan.items] == [
            "【日々の雑感】慎みは、いつから一滴ずつになったか"
        ]
        assert "\ufffd" not in plan.items[0].subject

    def test_mojibake_subject_is_skipped(self, tmp_path, usecase_factory):
        """U+FFFD が混じった件名は採らない（化けた値を送信済み件名にしない）"""
        write_file(tmp_path, "essay_body_20260811.txt", "本文", "2026-08-11 21:03:00")
        write_runner(
            tmp_path,
            "_send_20260811.py",
            OLD_LITERAL_RUNNER.format(
                body="essay_body_20260811.txt", subject="栓が一人\ufffdであること"
            ),
        )

        plan = usecase_factory().plan()

        assert plan.items == ()
        assert [s.body_file for s in plan.skipped] == ["essay_body_20260811.txt"]
        assert any("_send_20260811.py" in w for w in plan.warnings)

    @pytest.mark.parametrize(
        "name",
        [
            "_send_runner.py",
            "_send_driver.py",
            "_tmp_send_runner.py",
            "send_essay.py",
            "essay_waiter_temp.py",
        ],
    )
    def test_undated_runner_is_ignored(self, tmp_path, usecase_factory, name):
        """日付を持たない汎用ランナーの件名は、どの送信のものか決まらない

        実データの `_send_runner.py` / `_send_driver.py` は同じ `essay_body.txt`
        を名指す（本文は毎回上書きされていた）。採ると取り違えになる。
        """
        write_file(tmp_path, "essay_body.txt", "本文", "2026-08-17 21:06:00")
        write_runner(
            tmp_path,
            name,
            OLD_LITERAL_RUNNER.format(
                body="essay_body.txt", subject="日付のない正しさ"
            ),
        )

        plan = usecase_factory().plan()

        assert plan.items == ()
        assert [s.body_file for s in plan.skipped] == ["essay_body.txt"]

    def test_body_name_is_matched_whole(self, tmp_path, usecase_factory):
        """`essay_body.txt` は `_essay_body.txt` の参照に食い込まない"""
        write_file(tmp_path, "essay_body.txt", "本編", "2026-08-17 21:06:00")
        write_file(tmp_path, "_essay_body.txt", "別物", "2026-07-31 21:39:00")
        write_runner(
            tmp_path,
            "send_essay_20260817.py",
            LITERAL_RUNNER.format(
                body="essay_body.txt", subject="取りに行かないと、来ない期日"
            ),
        )

        plan = usecase_factory().plan()

        assert [i.body_file for i in plan.items] == ["essay_body.txt"]
        assert [s.body_file for s in plan.skipped] == ["_essay_body.txt"]

    def test_ambiguous_body_reference_is_reported(self, tmp_path, usecase_factory):
        """本文を 2 本名指すランナーは、どちらの送信か決まらないので採らない"""
        write_file(tmp_path, "essay_body_20260819.txt", "本文", "2026-08-19 22:04:00")
        write_file(tmp_path, "essay_body_20260820.txt", "本文", "2026-08-20 21:09:00")
        source = (
            LITERAL_RUNNER.format(body="essay_body_20260819.txt", subject="件名")
            + '\nFALLBACK = Path(r"C:\\x\\essay_body_20260820.txt")\n'
        )
        write_runner(tmp_path, "send_essay_20260819.py", source)

        plan = usecase_factory().plan()

        assert plan.items == ()
        assert any("send_essay_20260819.py" in w for w in plan.warnings)

    def test_runner_import_is_idempotent(self, tmp_path, usecase_factory):
        """③ 経由でも 2 回実行で台帳が二重にならない"""
        write_file(
            tmp_path, "essay_body_20260823.txt", "本文の中身\n", "2026-08-23 21:13:00"
        )
        write_runner(
            tmp_path,
            "send_essay_20260823.py",
            LITERAL_RUNNER.format(body="essay_body_20260823.txt", subject="件名"),
        )

        first = usecase_factory().execute()
        second = usecase_factory().execute()

        assert len(first) == 1
        assert second == []
        lines = (tmp_path / LEDGER_FILE_NAME).read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1
        assert len(list((tmp_path / SENT_DIR_NAME).iterdir())) == 1


# =============================================================================
# 台帳に既にある本文（実送信経路との二重計上）
# =============================================================================

BODY_NAME = "essay_body_20260828_2107.txt"
SUBJECT_NAME = "essay_subject_20260828_2107.txt"
BODY_WRITTEN_AT = "2026-08-28 21:07:00"
REAL_MESSAGE_ID = "<real@mail.gmail.com>"


def write_source_pair(directory: Path, body: str, encoding: str = "utf-8") -> None:
    """件名の出所つきで移行元の 1 通を置く（encoding は BOM の再現用）"""
    path = directory / BODY_NAME
    path.write_bytes(body.encode(encoding))
    stamp = datetime.fromisoformat(BODY_WRITTEN_AT).timestamp()
    os.utime(path, (stamp, stamp))
    write_file(directory, SUBJECT_NAME, "移行側の件名\n", BODY_WRITTEN_AT)


def record_in_ledger(directory: Path, body: str, message_id: str) -> None:
    """台帳へ 1 行記録する（sent/ に frontmatter 付きの本文ができる）"""
    LedgerStorageAdapter(PathResolverAdapter(base_dir=str(directory))).record_sent(
        message_id=message_id,
        sent_at="2026-08-28T21:15:34",
        subject="実送信の件名",
        recipient=RECIPIENT,
        body=body,
    )


class TestBodyAlreadyInLedger:
    """
    実送信ぶんとの二重計上を塞ぐ。実 Message-ID と合成 ID は突合できず、
    命名時刻と送信時刻もずれる（実測 8 分）ため、鍵は本文の内容そのもの。
    """

    def test_recorded_body_is_excluded(self, tmp_path, usecase_factory):
        """台帳に同一本文があれば、件名が復元できても取り込まない"""
        write_source_pair(tmp_path, "本文の中身\n")
        record_in_ledger(tmp_path, "本文の中身\n", REAL_MESSAGE_ID)

        plan = usecase_factory().plan()

        assert plan.items == ()
        assert [(s.body_file, s.reason) for s in plan.skipped] == [
            (BODY_NAME, RECORDED_BODY_REASON)
        ]

    def test_different_body_is_imported(self, tmp_path, usecase_factory):
        """本文が違えば取り込む（同じ日の別の一通を巻き添えにしない）"""
        write_source_pair(tmp_path, "移行する本文\n")
        record_in_ledger(tmp_path, "台帳にある別の本文\n", REAL_MESSAGE_ID)

        plan = usecase_factory().plan()

        assert [i.body_file for i in plan.items] == [BODY_NAME]

    def test_frontmatter_is_stripped_but_the_body_is_not(
        self, tmp_path, usecase_factory
    ):
        """frontmatter は剥がし、本文中の `---` 行は残す"""
        body = "序\n\n---\n\n結び\n"
        write_source_pair(tmp_path, body)
        record_in_ledger(tmp_path, body, REAL_MESSAGE_ID)
        sent = next((tmp_path / SENT_DIR_NAME).iterdir()).read_text(encoding="utf-8")
        assert sent.startswith("---")  # 比較相手に frontmatter が付いている前提

        plan = usecase_factory().plan()

        assert plan.items == ()

    def test_bom_in_the_source_still_matches(self, tmp_path, usecase_factory):
        """BOM 付きの移行元も一致する（U+FEFF は strip() では落ちない）"""
        write_source_pair(tmp_path, "本文の中身\n", encoding="utf-8-sig")
        record_in_ledger(tmp_path, "本文の中身\n", REAL_MESSAGE_ID)

        plan = usecase_factory().plan()

        assert plan.items == ()

    def test_migrated_body_stays_an_item(self, tmp_path, usecase_factory):
        """移行済み（合成 ID が台帳にある）は item のまま残る——ID の門が先"""
        write_source_pair(tmp_path, "本文の中身\n")
        record_in_ledger(
            tmp_path,
            "本文の中身\n",
            f"<legacy.{Path(BODY_NAME).stem}@emailingessay.invalid>",
        )

        plan = usecase_factory().plan()

        assert [i.body_file for i in plan.items] == [BODY_NAME]
