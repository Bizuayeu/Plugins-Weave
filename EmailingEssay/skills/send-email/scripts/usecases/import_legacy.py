# usecases/import_legacy.py
"""
遡及移行ユースケース

台帳が無かった頃の本文ファイルのうち、**実際に送った件名が復元できるものだけ**
を台帳へ取り込む。本文 1 行目やファイル名から件名を推定する経路は持たない——
台帳の全行が「実際に送った件名」で揃うことを、件数より優先する
（推定値を混ぜると、後から読む側が出所を判別できなくなる）。

件名の復元は 3 経路のみ:
  ① 日付付きの件名ファイル（`*essay_subject_<日付>[_サフィックス].txt`）
  ② `essay_wait.log` の SENT 行
  ③ 日付付き送信ランナー（`*send_<日付>*.py`）内の plain な件名リテラル
どれも無ければ移行しない。

既に台帳にある本文は取り込まない。突合鍵は本文の内容——実送信は実 Message-ID で
記録され、移行分は本文ファイル名から合成した ID を持つため、ID では突合できない。

移行元は読むだけ——削除も改変もしない（不可逆操作を移行に含めない）。

Stage 5: 遡及移行
"""

from __future__ import annotations

import ast
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

# 日付付き送信ランナー: `_send_20260611.py` / `send_20260815.py` /
# `send_essay_20260827_2112.py`。日付を持たない汎用ランナー（`_send_runner.py`
# `_send_driver.py` `_tmp_send_runner.py` `send_essay.py` `essay_waiter_temp.py`）は
# 対象外——それらは毎回上書きされる `essay_body.txt` を名指しており、件名が
# どの送信のものか決まらない（対応づけが推定になる）
RUNNER_GLOB = "*.py"
RUNNER_STEM_RE = re.compile(r"^_?send_(?:essay_)?\d{8}(?:_\w+)?$")

# 件名として採る代入先（`subject = "..."` / `SUBJECT = "..."`）
SUBJECT_NAMES = ("subject", "SUBJECT")

# 復号に失敗したバイトの置換文字。件名に混じっていれば化けている
REPLACEMENT_CHAR = "\ufffd"

# 作業ゴミの目印（IMPLEMENTATION_PLAN Stage 5 の列挙。`_tmp` は `_temp` と同族）
JUNK_PREFIXES = ("temp_", "tmp_")
JUNK_INFIXES = ("_tmp_", "_temp_")
JUNK_SUFFIXES = ("_latest", "_temp", "_tmp")

JUNK_REASON = "作業ゴミ"
NO_SOURCE_REASON = "件名の出所なし: 推定しない"
RECORDED_BODY_REASON = "台帳に同一本文あり"


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


@dataclass(frozen=True)
class _RunnerHit:
    """ランナーから得た 1 通分（件名が採れなければ reason に理由が入る）"""

    source: str  # `runner:<ファイル名>`
    subject: str | None
    reason: str | None


def _decode_source(path: Path) -> str | None:
    """
    ランナーを復号する（読み取り専用）。

    `_read_text()` の errors="replace" は使わない——化けた件名が「実際に送った
    値」として静かに台帳へ入る。utf-8 で読めなければ cp932 を試し（2026-08 に
    cp932 回避版へ書き直される前の世代がある）、どちらでも読めなければ諦める。

    Returns:
        復号できたソース。できなければ None
    """
    for encoding in ("utf-8-sig", "cp932"):
        try:
            return path.read_text(encoding=encoding)
        except (UnicodeDecodeError, OSError):
            continue
    return None


def _references(source: str, body_name: str) -> bool:
    """
    ランナーが本文ファイルを名指しているか。

    直前が名前の一部なら別物とする（`essay_body.txt` は `_essay_body.txt` の
    参照に食い込まない）。
    """
    pattern = rf"(?<![A-Za-z0-9_]){re.escape(body_name)}"
    return re.search(pattern, source) is not None


def _literal_subject(source: str) -> tuple[str | None, str | None]:
    """
    ランナーから件名を採る。

    採るのは `subject = "..."` / `SUBJECT = "..."` の plain な文字列リテラルだけ。
    ファイル参照・f-string・連結は「実際に送った値」がソースから決まらないため
    採らない（推定しない方針は ① ② と同じ）。

    Returns:
        (件名, 採れなかった理由)——どちらか一方だけが埋まる
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None, "ランナーを構文解析できない"

    literals: list[str] = []
    dynamic = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(t, ast.Name) and t.id in SUBJECT_NAMES for t in node.targets
        ):
            continue
        value = node.value
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            literals.append(value.value)
        else:
            dynamic = True

    if dynamic:
        return None, "件名が文字列リテラルでない: ファイル参照・連結・f-string"
    if len(set(literals)) != 1:
        return None, "件名リテラルが 1 つに決まらない"

    subject = literals[0].strip()
    if REPLACEMENT_CHAR in subject:
        return None, "件名が化けている: U+FFFD 混入"
    if not subject:
        return None, "件名が空"
    return subject, None


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

        known_ids = {record.message_id for record in self._ledger.load_records()}
        recorded = {body.strip() for body in self._ledger.load_sent_bodies()}

        warnings: list[str] = []
        subjects = self._restore_from_subject_files(candidates, warnings)
        log_hits = self._restore_from_wait_log(candidates, warnings)
        runner_hits = self._restore_from_runners(bodies, candidates, warnings)

        items: list[LegacyItem] = []
        skipped: list[LegacySkip] = []
        for path in bodies:
            if _is_junk(path):
                skipped.append(LegacySkip(path.name, JUNK_REASON))
                continue

            # 門は二段で、順序が要る。① 合成 ID が台帳にあれば移行済み——item の
            # まま残し、既出であることは呼び出し側に見せる。② それ以外で本文が
            # 台帳にあるなら、1.2.0 以降の実送信が実 Message-ID で記録した一通で、
            # 合成 ID では突合できない（本文の命名時刻と送信時刻もずれるので、
            # 時刻は鍵にならない）。逆順にすると移行済みの本文も `sent/` にある
            # ため候補が全滅する。
            # 同一本文の再送を重複と見なすのは意図した挙動（同じ文章を二度送った
            # なら台帳の一行で足りる）。
            message_id = _legacy_message_id(path)
            if message_id not in known_ids and self._body_recorded(path, recorded):
                skipped.append(LegacySkip(path.name, RECORDED_BODY_REASON))
                continue

            from_file = subjects.get(path.name)
            from_log = log_hits.get(path.name)
            from_runner = runner_hits.get(path.name)
            if from_file is not None:
                subject, source = from_file
            elif from_log is not None:
                subject, source = from_log.subject, from_log.source
            elif from_runner is not None and from_runner.subject is not None:
                subject, source = from_runner.subject, from_runner.source
            else:
                # ランナーはあったのに件名が採れなかった場合だけ理由を出す
                # （① ② で解決した本文のランナーまで報告すると警告が濁る）
                if from_runner is not None and from_runner.reason is not None:
                    warnings.append(
                        f"{path.name}: {from_runner.source}: {from_runner.reason}"
                    )
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
                    message_id=message_id,
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

    def _restore_from_runners(
        self, bodies: list[Path], candidates: list[Path], warnings: list[str]
    ) -> dict[str, _RunnerHit]:
        """
        ③ 日付付き送信ランナーの件名リテラルから復元する。

        本文との対応は、ランナーが実際に読んでいる本文ファイルの名前で取る
        （ファイル名パターンからの再構成ではない——世代ごとにランナーの書式は
        違うが、名指す本文は一つに決まる）。1 本のランナーが本文を 2 つ名指す、
        あるいは 1 本の本文を 2 本のランナーが名指す場合は、どちらの送信か
        決まらないので採らない。

        突合先は作業ゴミも含む全本文（`bodies`）——ゴミを名指すランナーを
        「本文参照が無い」と誤って報告しないため。復元するのは `candidates` だけ。

        Returns:
            本文ファイル名 -> _RunnerHit
        """
        body_names = [p.name for p in bodies]
        candidate_names = {p.name for p in candidates}

        claims: dict[str, list[_RunnerHit]] = {}
        for runner in sorted(self._source_dir.glob(RUNNER_GLOB)):
            if not runner.is_file() or not RUNNER_STEM_RE.match(runner.stem):
                continue
            source = f"runner:{runner.name}"

            text = _decode_source(runner)
            if text is None:
                warnings.append(f"{runner.name}: ランナーを復号できない")
                continue

            referenced = [name for name in body_names if _references(text, name)]
            if len(referenced) != 1:
                trouble = "無い" if not referenced else "曖昧"
                warnings.append(f"{runner.name}: 本文ファイル参照が{trouble}")
                continue

            body_name = referenced[0]
            if body_name not in candidate_names:
                continue  # 作業ゴミの本文——除外理由はゴミ側で出る

            subject, reason = _literal_subject(text)
            claims.setdefault(body_name, []).append(_RunnerHit(source, subject, reason))

        hits: dict[str, _RunnerHit] = {}
        for body_name, found in claims.items():
            if len({hit.subject for hit in found}) == 1:
                hits[body_name] = found[0]
                continue
            sources = " / ".join(hit.source for hit in found)
            hits[body_name] = _RunnerHit(
                sources, None, "複数のランナーが名指し、件名が決まらない"
            )
        return hits

    def _body_recorded(self, path: Path, recorded: set[str]) -> bool:
        """
        本文が既に台帳にあるか。

        照合用の読みは `utf-8-sig` strict——`_read_text()` の errors="replace" は
        使わない。BOM が残ると `str.strip()` では落ちず（空白ではない）、照合が
        黙って外れる。読めなければ一致なしとして候補に残す（取りこぼすより、
        重複を dry-run に見せる方が回復できる）。

        Args:
            path: 移行元の本文ファイル
            recorded: 台帳にある本文（strip 済み）

        Returns:
            台帳に同じ本文があれば True
        """
        try:
            body = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError):
            return False
        return body.strip() in recorded

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
