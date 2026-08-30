# adapters/cli/handlers.py
"""
コマンドハンドラレジストリ

main.pyの条件分岐ロジックをハンドラ関数に分離。
保守性と拡張性を向上させる。
"""

from __future__ import annotations

import re
import sys
from argparse import Namespace
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from domain.config import Config
from domain.thread_ref import ThreadRef, thread_ref_for
from domain.validators import validate_essay_body, validate_essay_subject
from frameworks.logging_config import get_logger
from usecases.factories import (
    create_import_legacy_usecase,
    create_ingest_replies_usecase,
    create_schedule_usecase,
    create_wait_usecase,
    get_ledger,
    get_mail_adapter,
)

from .decorators import validate_config

if TYPE_CHECKING:
    from usecases.import_legacy import LegacyItem, LegacyPlan

logger = get_logger("cli")

# ハンドラ型: argsを受け取り、終了コードを返す
Handler = Callable[[Namespace], int]

# 端末へ出してはいけない制御文字（C0 / DEL / C1）。空白扱いの TAB・LF・CR は
# 除いてあり、それらは後段の split() が区切りとして畳む
_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")


# =============================================================================
# メール系ハンドラ
# =============================================================================


@validate_config
def handle_test(args: Namespace) -> int:
    """テストメール送信"""
    mail = get_mail_adapter()
    mail.test()
    return 0


def _read_text_file(path: str) -> str:
    """
    件名・本文のファイルを読む。

    BOM 付きで保存された実ファイルを踏んでも壊れないよう utf-8-sig で読み、
    改行を LF に正規化して前後の空白を落とす（Domain の validator は LF だけを
    見る——正規化は Interface の責務）。cp932 フォールバックは持たない：
    読めない符号化はここで UnicodeDecodeError のまま上げ、main.py のログ経路に乗せる。

    Args:
        path: 読み込むファイルのパス

    Returns:
        BOM 無し・LF 正規化済みの本文
    """
    text = Path(path).read_text(encoding="utf-8-sig")
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


@validate_config
def handle_send(args: Namespace) -> int:
    """
    カスタムメール送信（--to-self なら自分宛の書き置き）。

    件名・本文はファイル（--subject-file / --body-file）でも渡せる。検証に落ちたら
    送信せずに 1 を返す——空本文や空行は届いてから直せない。

    宛先の別を問わず send_custom() を通す。整形もエスケープもそこに一本だけ
    置いてあるので、経路を分けた分だけ検疫を通らない便が生まれる。
    """
    subject = _read_text_file(args.subject_file) if args.subject_file else args.subject
    body = _read_text_file(args.body_file) if args.body_file else args.body

    errors = validate_essay_subject(subject) + validate_essay_body(body)
    if errors:
        for error in errors:
            logger.error(error)
            print(f"Error: {error}", file=sys.stderr)
        return 1

    to = Config.load().email.sender if args.to_self else ""
    get_mail_adapter().send_custom(
        subject, body, to=to, thread=_thread_for(args.in_reply_to)
    )
    return 0


def _thread_for(in_reply_to: str) -> ThreadRef | None:
    """
    --in-reply-to の値から紐づけ先を組む。

    台帳の返信を読むのは指定があるときだけ——紐づけない送信に I/O を課さない。

    Args:
        in_reply_to: 紐づけ先の Message-ID（空なら紐づけない）

    Returns:
        組み上がった ThreadRef。指定が無ければ None
    """
    if not in_reply_to:
        return None
    return thread_ref_for(in_reply_to, get_ledger().load_replies())


# =============================================================================
# 待機ハンドラ
# =============================================================================


def handle_wait(args: Namespace) -> int:
    """待機コマンド（list または spawn）"""
    waiter = create_wait_usecase()

    if args.time == "list":
        waiters = waiter.list_waiters()
        if not waiters:
            print("No active waiting processes.")
            return 0
        print(f"Active waiting processes: {len(waiters)}")
        print("-" * 60)
        for w in waiters:
            pid = w.get("pid", "?")
            target = w.get("target_time", "?")
            theme = w.get("theme", "") or "(no theme)"
            registered = w.get("registered_at", "?")
            print(f"  PID: {pid}")
            print(f"    Target: {target}")
            print(f"    Theme:  {theme}")
            print(f"    Registered: {registered}")
            print()
        return 0

    waiter.spawn(
        target_time=args.time,
        theme=args.theme,
        context=args.context,
        file_list=args.file_list,
        lang=args.lang,
    )
    return 0


# =============================================================================
# 返信サブハンドラ
# =============================================================================


@validate_config
def _handle_replies_fetch(args: Namespace) -> int:
    """受信箱から返信を取り込む"""
    usecase = create_ingest_replies_usecase()
    # 件数は usecase が INFO 1 行で報告する（logger の StreamHandler は stdout。
    # ここで print すると同じ行が二重に出る）
    usecase.fetch()
    return 0


def _terminal_safe(value: str) -> str:
    """
    外部入力を端末へ出す前に検疫する。

    件名は取り込みの 4 関門を通った差出人が書いた値だが、ANSI エスケープや
    改行を素で流せば一覧の行そのものを偽装できる。文字は削らず、制御文字だけを
    落として空白で畳む——読めなくするより、行が崩れないことを採る。

    Args:
        value: 表示したい外部入力

    Returns:
        制御文字を含まない 1 行の文字列
    """
    return " ".join(_CONTROL_CHARS_RE.sub("", value).split())


def _handle_replies_list(args: Namespace) -> int:
    """
    取り込み済み返信の一覧（本文は出さない）。

    本文は外部入力であり、端末やログへ素で流す経路を作らない
    （読むときは essay_replies.jsonl を data として開く — ops-rules 7）。
    件名だけは索引として要るので、制御文字を落としてから 1 行で出す。
    台帳を読むだけなので資格情報を要さない。
    """
    replies = get_ledger().load_replies()
    if not replies:
        print("No replies ingested yet.")
        return 0

    print(f"Ingested replies: {len(replies)}")
    print("-" * 60)
    for r in replies:
        print(f"  Message-ID: {r.message_id}")
        print(f"    Subject:     {_terminal_safe(r.subject)}")
        print(f"    In-Reply-To: {r.in_reply_to}")
        print(f"    From:        {r.sender}")
        print(f"    Received:    {r.received_at}")
        print()
    return 0


# 返信サブコマンドのレジストリ
REPLIES_HANDLERS: dict[str, Handler] = {
    "fetch": _handle_replies_fetch,
    "list": _handle_replies_list,
}


def handle_replies(args: Namespace) -> int:
    """返信コマンド（サブコマンドにディスパッチ）"""
    handler = REPLIES_HANDLERS.get(args.replies_cmd)
    if not handler:
        print(f"Unknown replies subcommand: {args.replies_cmd}")
        return 1
    return handler(args)


# =============================================================================
# 台帳サブハンドラ
# =============================================================================


def _print_legacy_items(items: list[LegacyItem]) -> None:
    """
    移行対象を 1 件ずつ並べる。

    件数だけでは取り違えを検出できない（本文を 1 本入れ替えても件数は同じ）。
    どの本文にどの件名がどの出所から付くのかを出す。
    """
    for item in items:
        print(f"  {item.sent_at}  {item.body_file}")
        print(f"    subject: {item.subject}")
        print(f"    source:  {item.subject_source}")
        print(f"    id:      {item.message_id}")


def _print_legacy_plan(plan: LegacyPlan, known_ids: frozenset[str]) -> None:
    """
    移行計画を検品できる形で出す。

    plan() も台帳を見る（本文が既に記録済みの候補は除外して返る）が、移行済みの
    一件は item のまま残る。それを既出分と新規分に分けるのはここ——総数だけでは
    「今回何件増えるのか」が読めない。

    Args:
        plan: 移行計画
        known_ids: 台帳に既にある message_id
    """
    new_items = [i for i in plan.items if i.message_id not in known_ids]
    already = [i for i in plan.items if i.message_id in known_ids]

    print(f"Import candidates: {len(plan.items)}")
    print(f"  new:               {len(new_items)}")
    print(f"  already in ledger: {len(already)}")
    print("-" * 60)
    print(f"New ({len(new_items)}):")
    _print_legacy_items(new_items)
    print()
    print(f"Already in the ledger ({len(already)}):")
    _print_legacy_items(already)
    print()
    print(f"Excluded: {len(plan.skipped)}")
    print("-" * 60)
    for skip in plan.skipped:
        print(f"  {skip.body_file} — {skip.reason}")
    print()
    if plan.warnings:
        print(f"Warnings: {len(plan.warnings)}")
        for warning in plan.warnings:
            print(f"  {warning}")
        print()


@validate_config
def _handle_ledger_import_legacy(args: Namespace) -> int:
    """
    過去の本文を台帳へ遡及移行する。

    --dry-run は計画を出すだけで何も書かない（plan() は書き込み経路を持たない）。
    移行元は読むだけ——削除も改変もしない。
    """
    usecase = create_import_legacy_usecase()
    known_ids = frozenset(record.message_id for record in get_ledger().load_records())

    if args.dry_run:
        print("Dry run: nothing is written.")
        _print_legacy_plan(usecase.plan(), known_ids)
        return 0

    _print_legacy_plan(usecase.plan(), known_ids)
    records = usecase.execute()
    print(f"Imported: {len(records)}")
    return 0


# 台帳サブコマンドのレジストリ
LEDGER_HANDLERS: dict[str, Handler] = {
    "import-legacy": _handle_ledger_import_legacy,
}


def handle_ledger(args: Namespace) -> int:
    """台帳コマンド（サブコマンドにディスパッチ）"""
    handler = LEDGER_HANDLERS.get(args.ledger_cmd)
    if not handler:
        print(f"Unknown ledger subcommand: {args.ledger_cmd}")
        return 1
    return handler(args)


# =============================================================================
# スケジュールサブハンドラ
# =============================================================================


def _handle_schedule_list(args: Namespace) -> int:
    """スケジュール一覧"""
    usecase = create_schedule_usecase()
    usecase.list()
    return 0


def _handle_schedule_remove(args: Namespace) -> int:
    """スケジュール削除"""
    usecase = create_schedule_usecase()
    usecase.remove(args.name)
    return 0


def _handle_schedule_add(args: Namespace, frequency: str) -> int:
    """ジェネリックスケジュール追加ハンドラ"""
    usecase = create_schedule_usecase()
    usecase.add(
        frequency=frequency,
        time_spec=args.time,
        weekday=getattr(args, "weekday", ""),
        theme=args.theme,
        context_file=args.context,
        file_list=args.file_list,
        lang=args.lang,
        name=args.name,
        day_spec=getattr(args, "day_spec", ""),
    )
    return 0


# スケジュールサブコマンドのレジストリ
SCHEDULE_HANDLERS: dict[str, Handler] = {
    "list": _handle_schedule_list,
    "remove": _handle_schedule_remove,
    "daily": lambda args: _handle_schedule_add(args, "daily"),
    "weekly": lambda args: _handle_schedule_add(args, "weekly"),
    "monthly": lambda args: _handle_schedule_add(args, "monthly"),
}


def handle_schedule(args: Namespace) -> int:
    """スケジュールコマンド（サブコマンドにディスパッチ）"""
    handler = SCHEDULE_HANDLERS.get(args.schedule_cmd)
    if not handler:
        print(f"Unknown schedule subcommand: {args.schedule_cmd}")
        return 1
    return handler(args)


# =============================================================================
# メインハンドラレジストリ
# =============================================================================

HANDLERS: dict[str, Handler] = {
    "test": handle_test,
    "send": handle_send,
    "wait": handle_wait,
    "replies": handle_replies,
    "ledger": handle_ledger,
    "schedule": handle_schedule,
}


def dispatch(args: Namespace) -> int:
    """
    コマンドをディスパッチする。

    Args:
        args: パース済み引数

    Returns:
        終了コード（-1: コマンド未指定、0: 成功、1: エラー）
    """
    if not args.command:
        return -1  # ヘルプ表示シグナル

    handler = HANDLERS.get(args.command)
    if not handler:
        print(f"Unknown command: {args.command}")
        return 1

    return handler(args)


__all__ = ["HANDLERS", "LEDGER_HANDLERS", "REPLIES_HANDLERS", "dispatch"]
