"""ポーリング窓の不変条件を bootstrap.sh と gateway 定数の突合で張る。

窓 (`TELEGRAM_SECRETARY_POLL_SET_SEC`) と HTTP 再試行予算 (`TelegramApiGateway` の
`retry_count` / `request_timeout`) は別ファイルに住んでいて、互いを知らない。両者の和が
bash tool の timeout を超えると watch が SIGTERM (exit 143) で落ちる——実際 2026-08-15 に
502 が続いた枠が落ちた。窓 540 は「最悪滞留 = long-poll の --timeout(30s)」という誤った
見積もりの上に立っていたが、平常時は 502 が出ないので条件が破れていることが見えなかった。

同種の腐りは「コメントに書いた不変条件」では止まらない（現に止まらなかった）ので、
値そのものを突合してテストの失敗として出す。片方だけ動かしたら赤になる。
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import pytest
from adapters.telegram.api_gateway import TelegramApiGateway

BOOTSTRAP = Path(__file__).parents[3] / "bootstrap.sh"

# 窓満了後、プロセスが exit するまでに残る仕事（emit / lease renew / インタプリタ終了）の余裕。
# **仮置き**（実測ではない）——bash timeout はちょうど 600s で発火するので余裕ゼロでは競走になる、
# という理由だけで置いた値。昇格トリガー = 窓満了から exit までを実測できた枠があれば、その値で校正する。
POST_FETCH_MARGIN_SEC = 30


def _shell_default(var: str) -> int:
    """`export VAR="${VAR:-N}"` の N を bootstrap.sh から読む（見つからなければ失敗）。"""
    text = BOOTSTRAP.read_text(encoding="utf-8")
    match = re.search(rf'export {var}="\$\{{{var}:-(\d+)\}}"', text)
    assert match, f"{var} の既定値を bootstrap.sh から読めない（行の書式が変わった？）"
    return int(match.group(1))


def _gateway_default(param: str) -> float:
    value = inspect.signature(TelegramApiGateway.__init__).parameters[param].default
    assert value is not inspect.Parameter.empty, f"{param} に既定値が無い"
    return value


def test_poll_window_fits_bash_timeout_with_retry_budget():
    """窓 + 1 サイクルの最悪滞留 + 後処理余裕 <= bash timeout。

    最悪滞留は long-poll の --timeout ではなく `(retry_count + 1) * request_timeout`。
    5xx は sleep せず即再試行するので、待ちではなく試行回数が時間を食う。
    """
    window = _shell_default("TELEGRAM_SECRETARY_POLL_SET_SEC")
    bash_timeout = _shell_default("TELEGRAM_SECRETARY_POLL_BASH_TIMEOUT_MS") / 1000
    worst_fetch = (_gateway_default("retry_count") + 1) * _gateway_default(
        "request_timeout"
    )

    assert window + worst_fetch + POST_FETCH_MARGIN_SEC <= bash_timeout, (
        f"窓 {window}s + 最悪滞留 {worst_fetch}s + 余裕 {POST_FETCH_MARGIN_SEC}s が "
        f"bash timeout {bash_timeout}s を超える（SIGTERM する）。"
        f"窓を下げるか、fetch の総予算を残り窓へ丸める"
    )


def test_max_turns_floor_holds_for_the_configured_window():
    """窓を縮めてもアイドル下限 (duration/窓) が MAX_TURNS の floor 30 を割らない。

    窓は MAX_TURNS の算出式 `duration/窓 + 15*duration/3600` にも入る。窓を縮めると
    アイドル枠のターン数が増える（コスト側の副作用）——floor 30 に当たると
    「アイドルで回りきる前に日次上限で沈黙する」ので、実運用 duration では割らないことを張る。
    """
    window = _shell_default("TELEGRAM_SECRETARY_POLL_SET_SEC")
    four_hours = 14400
    idle_turns = four_hours // window
    max_turns = idle_turns + 15 * four_hours // 3600

    assert idle_turns <= max_turns, "アイドル下限が総量上限を超える"
    assert max_turns >= 30, "MAX_TURNS が floor を割る（窓が長すぎる）"


@pytest.mark.parametrize(
    "var",
    ["TELEGRAM_SECRETARY_POLL_SET_SEC", "TELEGRAM_SECRETARY_POLL_BASH_TIMEOUT_MS"],
)
def test_bootstrap_exposes_override(var):
    """両値とも env で上書き可能な形（`${VAR:-N}`）で export されている。"""
    assert _shell_default(var) > 0
