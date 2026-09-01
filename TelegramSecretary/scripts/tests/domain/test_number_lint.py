from __future__ import annotations

from domain.number_lint import lint_numbers


def test_bare_number_line_is_reported_with_line_number():
    report = lint_numbers("裸率は 58.3% だった。\n所感を書く。")
    assert report.number_lines == 1
    assert report.covered == 0
    assert report.bare == 1
    assert report.bare_lines == [(1, "裸率は 58.3% だった。")]


def test_gauge_token_on_the_same_line_covers_it():
    report = lint_numbers("実測で 34 件だった。")
    assert report.number_lines == 1
    assert report.covered == 1
    assert report.bare == 0
    assert report.bare_lines == []


def test_text_without_digits_still_returns_the_structure():
    report = lint_numbers("数字を含まない本文。\nもう一行。")
    assert report.number_lines == 0
    assert report.covered == 0
    assert report.bare == 0
    assert report.bare_lines == []


def test_fullwidth_digits_are_detected_as_bare():
    report = lint_numbers("残りは３４件です。")
    assert report.number_lines == 1
    assert report.bare == 1
    assert report.bare_lines == [(1, "残りは３４件です。")]


def test_empty_text_is_an_empty_report():
    report = lint_numbers("")
    assert report.number_lines == 0
    assert report.bare_lines == []


def test_gauge_token_covers_only_its_own_line():
    text = "実測で 34 件。\nうち 12 件が該当。"
    report = lint_numbers(text)
    assert report.number_lines == 2
    assert report.covered == 1
    assert report.bare == 1
    assert report.bare_lines == [(2, "うち 12 件が該当。")]


def test_stem_tokens_match_their_inflections():
    # 「見積」「引き写」は語幹として置いてある（見積もり / 引き写した を部分一致で拾う）
    assert lint_numbers("見積もりで 300 万円。").bare == 0
    assert lint_numbers("前回値を引き写した 12 件。").bare == 0
