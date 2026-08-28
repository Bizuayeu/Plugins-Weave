# usecases/import_legacy.py
"""
遡及移行ユースケース

台帳が無かった頃の本文ファイルのうち、**実際に送った件名が復元できるものだけ**
を台帳へ取り込む。本文 1 行目やファイル名から件名を推定する経路は持たない——
台帳の全行が「実際に送った件名」で揃うことを、件数より優先する
（推定値を混ぜると、後から読む側が出所を判別できなくなる）。

件名の復元は 2 経路のみ:
  ① 日付付きの件名ファイル（`*essay_subject_<日付>[_サフィックス].txt`）
  ② `essay_wait.log` の SENT 行
どちらも無ければ移行しない。

移行元は読むだけ——削除も改変もしない（不可逆操作を移行に含めない）。

Stage 5: 遡及移行
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from frameworks.logging_config import get_logger

if TYPE_CHECKING:
    from domain.models import LedgerRecord

    from .ports import LedgerPort

logger = get_logger("import_legacy")

__all__ = ["ImportLegacyUseCase", "LegacyItem", "LegacyPlan", "LegacySkip"]

# 移行元の実体（`~/.claude/plugins/.emailingessay/`）で実測した命名
BODY_GLOB = "*essay_body*"
WAIT_LOG_NAME = "essay_wait.log"

# 日付付き件名ファイル: `_essay_subject_20260724` / `essay_subject_20260814_pm`
SUBJECT_STEM_RE = re.compile(r"^.*essay_subject_\d{8}(?:_\w+)?$")

# SENT 行: `[2026-07-30 21:40:18] non-interactive essay SENT to a@b | subject=...`
SENT_LINE_RE = re.compile(
    r"^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]"
    r".*\bSENT\b to (?P<to>\S+) \| subject=(?P<subject>.*)$"
)

# 作業ゴミの目印（IMPLEMENTATION_PLAN Stage 5 の列挙。`_tmp` は `_temp` と同族）
JUNK_PREFIXES = ("temp_", "tmp_")
JUNK_INFIXES = ("_tmp_", "_temp_")
JUNK_SUFFIXES = ("_latest", "_temp", "_tmp")

JUNK_REASON = "作業ゴミ"
NO_SOURCE_REASON = "件名の出所なし: 推定しない"


@dataclass(frozen=True)
class LegacyItem:
    """移行する 1 通分"""

    body_file: str  # 移行元の本文ファイル名（読むだけ）
    subject: str
    subject_source: str  # 件名の出所（dry-run の検品用）
    sent_at: str  # ISO 8601
    recipient: str
    message_id: str


@dataclass(frozen=True)
class LegacySkip:
    """移行しない 1 本と、その理由"""

    body_file: str
    reason: str


@dataclass(frozen=True)
class LegacyPlan:
    """移行計画（作るだけで、何も書かない）"""

    items: tuple[LegacyItem, ...]
    skipped: tuple[LegacySkip, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class _LogHit:
    """SENT 行から得た 1 通分"""

    subject: str
    source: str
    sent_at: str
    recipient: str


def _is_junk(path: Path) -> bool:
    """作業ゴミか判定する"""
    stem = path.stem
    return (
        stem.startswith(JUNK_PREFIXES)
        or any(infix in stem for infix in JUNK_INFIXES)
        or stem.endswith(JUNK_SUFFIXES)
    )


def _mtime(path: Path) -> datetime:
    """本文が書かれた時刻（送信の直前）"""
    return datetime.fromtimestamp(path.stat().st_mtime).replace(microsecond=0)


def _legacy_message_id(path: Path) -> str:
    """
    移行分の Message-ID を採番する。

    実際に送られた Message-ID は残っていない（台帳が無かった頃の送信は
    yagmail が採番し、どこにも記録されていない）。よって移行分と分かる形の
    合成 ID を、本文ファイル名から決定論的に作る。同じ本文は何度計算しても
    同じ ID になり、二重取り込みは台帳側の冪等判定が弾く。
    ドメインは RFC 2606 の `.invalid`——実在の Message-ID と取り違えられない。
    """
    return f"<legacy.{path.stem}@emailingessay.invalid>"


class ImportLegacyUseCase:
    """遡及移行ユースケース"""

    def __init__(self, source_dir: str, ledger: LedgerPort, recipient: str) -> None:
        """
        Args:
            source_dir: 移行元ディレクトリ（読み取りのみ）
            ledger: LedgerPort 実装（追記先）
            recipient: 宛先の既定値（SENT 行に宛先がある場合はそちらを使う）
        """
        self._source_dir = Path(source_dir)
        self._ledger = ledger
        self._recipient = recipient

    # -------------------------------------------------------------------------
    # 計画（何も書かない）
    # -------------------------------------------------------------------------

    def plan(self) -> LegacyPlan:
        """
        移行計画を作る。ファイルは一切書かない（dry-run の実体）。

        Returns:
            取り込み対象・除外対象・突合の異常
        """
        bodies = sorted(
            (p for p in self._source_dir.glob(BODY_GLOB) if p.is_file()),
            key=lambda p: p.name,
        )
        candidates = [p for p in bodies if not _is_junk(p)]

        warnings: list[str] = []
        subjects = self._restore_from_subject_files(candidates, warnings)
        log_hits = self._restore_from_wait_log(candidates, warnings)

        items: list[LegacyItem] = []
        skipped: list[LegacySkip] = []
        for path in bodies:
            if _is_junk(path):
                skipped.append(LegacySkip(path.name, JUNK_REASON))
                continue

            from_file = subjects.get(path.name)
            from_log = log_hits.get(path.name)
            if from_file is not None:
                subject, source = from_file
            elif from_log is not None:
                subject, source = from_log.subject, from_log.source
            else:
                skipped.append(LegacySkip(path.name, NO_SOURCE_REASON))
                continue

            if from_file and from_log and from_file[0] != from_log.subject:
                warnings.append(
                    f"{path.name}: 件名が 2 経路で食い違う: "
                    f"{from_file[1]} / {from_log.source}"
                )

            items.append(
                LegacyItem(
                    body_file=path.name,
                    subject=subject,
                    subject_source=source,
                    # 送信時刻はログ行が確か。無ければ本文の書き込み時刻で近似する
                    sent_at=from_log.sent_at if from_log else _mtime(path).isoformat(),
                    recipient=from_log.recipient if from_log else self._recipient,
                    message_id=_legacy_message_id(path),
                )
            )

        items.sort(key=lambda i: (i.sent_at, i.body_file))
        return LegacyPlan(tuple(items), tuple(skipped), tuple(warnings))

    def _restore_from_subject_files(
        self, candidates: list[Path], warnings: list[str]
    ) -> dict[str, tuple[str, str]]:
        """
        ① 日付付き件名ファイルから復元する。

        本文との対応は、ファイル名の `subject` を `body` に置き換えた名前で取る
        （`_pm` / `_2122` のような同日 2 通目のサフィックスまで含めて一致させる）。

        Returns:
            本文ファイル名 -> (件名, 出所)
        """
        names = {p.name for p in candidates}
        restored: dict[str, tuple[str, str]] = {}
        for path in sorted(self._source_dir.glob("*essay_subject_*")):
            if not path.is_file() or not SUBJECT_STEM_RE.match(path.stem):
                continue
            body_name = path.name.replace("essay_subject_", "essay_body_", 1)
            if body_name not in names:
                warnings.append(f"{path.name}: 対応する本文が見つからない")
                continue
            subject = self._read_text(path).strip()
            if not subject:
                warnings.append(f"{path.name}: 件名が空")
                continue
            restored[body_name] = (subject, f"subject-file:{path.name}")
        return restored

    def _restore_from_wait_log(
        self, candidates: list[Path], warnings: list[str]
    ) -> dict[str, _LogHit]:
        """
        ② `essay_wait.log` の SENT 行から復元する。

        SENT 行は送信の直後に書かれ、本文はその直前に書かれている。よって
        「その時刻以前で最も新しい、同じ日の本文」を対応先とする。1 本の本文を
        2 行が取り合わないよう、確定した本文は候補から外す。

        Returns:
            本文ファイル名 -> _LogHit
        """
        log_path = self._source_dir / WAIT_LOG_NAME
        if not log_path.is_file():
            return {}

        mtimes = {p: _mtime(p) for p in candidates}
        hits: dict[str, _LogHit] = {}
        for line in self._read_text(log_path).splitlines():
            matched = SENT_LINE_RE.match(line)
            if not matched:
                continue
            sent_at = datetime.strptime(matched["ts"], "%Y-%m-%d %H:%M:%S")
            pool = [
                p
                for p, written in mtimes.items()
                if p.name not in hits
                and written <= sent_at
                and written.date() == sent_at.date()
            ]
            if not pool:
                warnings.append(
                    f"SENT 行に対応する本文が見つからない: "
                    f"[{matched['ts']}] {matched['subject']}"
                )
                continue
            body = max(pool, key=lambda p: mtimes[p])
            hits[body.name] = _LogHit(
                subject=matched["subject"].strip(),
                source=f"wait-log:{matched['ts']}",
                sent_at=sent_at.isoformat(),
                recipient=matched["to"],
            )
        return hits

    def _read_text(self, path: Path) -> str:
        """
        移行元を読む（読み取り専用）。

        読めないバイトで全体を落とさない——移行元は cp932 混入の可能性がある
        手書きログを含む。
        """
        return path.read_text(encoding="utf-8", errors="replace")

    # -------------------------------------------------------------------------
    # 実行（台帳への追記のみ）
    # -------------------------------------------------------------------------

    def execute(self) -> list[LedgerRecord]:
        """
        計画どおりに台帳へ追記する。移行元には一切書き戻さない。

        Returns:
            今回新たに記録された LedgerRecord（既出分は含まない）
        """
        plan = self.plan()
        recorded: list[LedgerRecord] = []
        for item in plan.items:
            record = self._ledger.record_sent(
                message_id=item.message_id,
                sent_at=item.sent_at,
                subject=item.subject,
                recipient=item.recipient,
                body=self._read_text(self._source_dir / item.body_file),
            )
            if record is not None:
                recorded.append(record)

        logger.debug(f"Imported legacy records: {len(recorded)}/{len(plan.items)}")
        return recorded
