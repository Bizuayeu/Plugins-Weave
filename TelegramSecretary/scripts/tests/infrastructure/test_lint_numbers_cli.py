"""lint-numbers CLI（読み取り専用・JSON 1 行）の契約テスト。

handler を Namespace 直呼びする（`test_registry_cli.py` の流儀）。config / lease /
レジストリに触れない経路なので env fixture を要さない。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from infrastructure.exit_codes import EXIT_CONFIG_INVALID, EXIT_OK
from main import cmd_lint_numbers

_BARE_2_COVERED_1 = "\n".join(
    [
        "見出し（数字なし）",
        "handoff は 34 件だった",  # 2 行目: 裸
        "実測で 12 件を数えた",  # 3 行目: covered
        "残りは ３ 件",  # 4 行目: 裸（全角）
    ]
)


def _ns(path: Path) -> argparse.Namespace:
    return argparse.Namespace(path=str(path))


def test_bare_lines_counted_and_numbered(tmp_path, capsys):
    """裸 2 行・covered 1 行 → EXIT_OK、bare == 2、行番号が一致する。"""
    target = tmp_path / "deliverable.md"
    target.write_text(_BARE_2_COVERED_1, encoding="utf-8")

    assert cmd_lint_numbers(_ns(target)) == EXIT_OK

    out = capsys.readouterr().out
    assert out.count("\n") == 1  # JSON 1 行
    report = json.loads(out)
    assert report["path"] == str(target)
    assert report["number_lines"] == 3
    assert report["covered"] == 1
    assert report["bare"] == 2
    assert [line_no for line_no, _ in report["bare_lines"]] == [2, 4]


def test_zero_bare_still_prints_json(tmp_path, capsys):
    """裸 0 件でも黙らない（掛け忘れと全緑を区別させるため JSON 1 行を必ず出す）。"""
    target = tmp_path / "clean.md"
    target.write_text("実測で 12 件を数えた\n", encoding="utf-8")

    assert cmd_lint_numbers(_ns(target)) == EXIT_OK

    out = capsys.readouterr().out
    report = json.loads(out)
    assert report["bare"] == 0
    assert report["bare_lines"] == []
    assert report["covered"] == 1


def test_missing_path_returns_config_invalid(tmp_path, capsys):
    """不在パス → stderr 一行 ＋ EXIT_CONFIG_INVALID（cmd_render_pdf と同型）。"""
    missing = tmp_path / "nope.md"

    assert cmd_lint_numbers(_ns(missing)) == EXIT_CONFIG_INVALID

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
    assert "lint-numbers" in captured.err
