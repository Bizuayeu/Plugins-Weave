#!/usr/bin/env python3
"""
Link Checker Tests
==================

tools/link_checker.py のテスト

テストケース:
1. 有効な相対リンクの検出
2. 壊れたリンクの検出
3. アンカーリンクの検証
4. ネストしたディレクトリのリンク解決
5. 外部リンク（http/https）のスキップ
6. 空のドキュメントディレクトリ処理
7. サマリー生成
"""

from pathlib import Path

import pytest

from tools.link_checker import (
    CheckSummary,
    LinkCheckResult,
    LinkStatus,
    MarkdownLinkChecker,
)


@pytest.fixture
def temp_docs_dir(tmp_path: Path):
    """テスト用ドキュメントディレクトリ"""
    docs = tmp_path / "docs"
    docs.mkdir()
    return docs


class TestMarkdownLinkChecker:
    """MarkdownLinkChecker のテスト"""

    def test_valid_relative_link(self, temp_docs_dir) -> None:
        """有効な相対リンクの検出"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file2 = temp_docs_dir / "guide.md"

        file1.write_text("# Index\n\nSee [Guide](guide.md) for details.", encoding="utf-8")
        file2.write_text("# Guide\n\nThis is a guide.", encoding="utf-8")

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value
        assert results[0].link_target == "guide.md"

    def test_broken_link_detection(self, temp_docs_dir) -> None:
        """壊れたリンクの検出"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text("# Index\n\n[Missing](nonexistent.md)", encoding="utf-8")

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.BROKEN.value
        assert results[0].suggestion is not None

    def test_anchor_validation_valid(self, temp_docs_dir) -> None:
        """有効なアンカーリンクの検証"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "# Index\n\n## Section One\n\nSee [Section One](#section-one)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_anchor_validation_missing(self, temp_docs_dir) -> None:
        """存在しないアンカーの検出"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text("# Index\n\n[Missing](#nonexistent-section)", encoding="utf-8")

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.ANCHOR_MISSING.value

    def test_file_with_anchor(self, temp_docs_dir) -> None:
        """ファイル+アンカーの複合検証"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file2 = temp_docs_dir / "guide.md"

        file1.write_text("[Guide Setup](guide.md#setup)", encoding="utf-8")
        file2.write_text("# Guide\n\n## Setup\n\nSetup instructions.", encoding="utf-8")

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_nested_directory_resolution(self, temp_docs_dir) -> None:
        """ネストしたディレクトリのリンク解決"""
        # Setup
        subdir = temp_docs_dir / "dev"
        subdir.mkdir()

        file1 = temp_docs_dir / "index.md"
        file2 = subdir / "api.md"

        file1.write_text("[API](dev/api.md)", encoding="utf-8")
        file2.write_text("# API Reference", encoding="utf-8")

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_parent_directory_link(self, temp_docs_dir) -> None:
        """親ディレクトリへのリンク解決"""
        # Setup
        subdir = temp_docs_dir / "dev"
        subdir.mkdir()

        file1 = temp_docs_dir / "index.md"
        file2 = subdir / "api.md"

        file1.write_text("# Index", encoding="utf-8")
        file2.write_text("[Back to Index](../index.md)", encoding="utf-8")

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_external_link_skip(self, temp_docs_dir) -> None:
        """外部リンク（http/https）のスキップ"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "[GitHub](https://github.com)\n[HTTP](http://example.com)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 2
        assert all(r.status == LinkStatus.EXTERNAL.value for r in results)

    def test_empty_directory(self, temp_docs_dir) -> None:
        """空のドキュメントディレクトリ処理"""
        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 0

    def test_summary_generation(self, temp_docs_dir) -> None:
        """サマリー生成"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file2 = temp_docs_dir / "guide.md"

        file1.write_text(
            "[Valid](guide.md)\n[Broken](missing.md)\n[External](https://example.com)",
            encoding="utf-8",
        )
        file2.write_text("# Guide", encoding="utf-8")

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        checker.check_all()
        summary = checker.get_summary()

        # Verify
        assert summary.total_files == 1
        assert summary.total_links == 3
        assert summary.valid == 1
        assert summary.broken == 1
        assert summary.external == 1

    def test_get_broken_links(self, temp_docs_dir) -> None:
        """壊れたリンクのみ取得"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "[Valid](index.md)\n[Broken](missing.md)\n[Anchor](#missing)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        checker.check_all()
        broken = checker.get_broken_links()

        # Verify
        assert len(broken) == 2
        statuses = {r.status for r in broken}
        assert LinkStatus.BROKEN.value in statuses
        assert LinkStatus.ANCHOR_MISSING.value in statuses

    def test_japanese_heading_anchor(self, temp_docs_dir) -> None:
        """日本語見出しのアンカー検証"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "# はじめに\n\n## セットアップ\n\n[セットアップ](#セットアップ)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_multiple_links_in_one_line(self, temp_docs_dir) -> None:
        """1行に複数のリンク"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file2 = temp_docs_dir / "a.md"
        file3 = temp_docs_dir / "b.md"

        file1.write_text("See [A](a.md) and [B](b.md) for details.", encoding="utf-8")
        file2.write_text("# A", encoding="utf-8")
        file3.write_text("# B", encoding="utf-8")

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 2
        assert all(r.status == LinkStatus.VALID.value for r in results)

    def test_link_check_result_to_dict(self, temp_docs_dir) -> None:
        """LinkCheckResult の辞書変換"""
        result = LinkCheckResult(
            file_path="index.md",
            line_number=1,
            link_text="Test",
            link_target="test.md",
            status=LinkStatus.VALID.value,
            suggestion=None,
        )

        d = result.to_dict()

        assert d["file_path"] == "index.md"
        assert d["line_number"] == 1
        assert d["status"] == "valid"

    def test_nonexistent_docs_dir(self, tmp_path: Path) -> None:
        """存在しないディレクトリの処理"""
        nonexistent = tmp_path / "nonexistent"

        checker = MarkdownLinkChecker(nonexistent)
        results = checker.check_all()

        assert len(results) == 0

    def test_nakaguro_stripped_from_anchor(self, temp_docs_dir) -> None:
        """中黒（・）がアンカーから除去されることを確認（GitHub互換）"""
        # Setup - 見出しに中黒があるが、アンカーは中黒なしで参照
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "# 導入・セットアップ\n\n[リンク](#導入セットアップ)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - GitHubと同じく中黒を除去するのでVALID
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_nakaguro_in_link_not_auto_stripped(self, temp_docs_dir) -> None:
        """中黒を含むアンカーリンクは自動除去されない（GitHub互換の厳密モード）

        GitHubでは見出しからアンカーを生成する際に中黒を除去するが、
        リンクのアンカー部分は変換されない。そのため、中黒を含むリンクは
        中黒なしのアンカーとマッチしない。
        """
        # Setup - 見出しには中黒あり、アンカーにも中黒あり
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "# マルチユーザー・同時アクセス\n\n[リンク](#マルチユーザー・同時アクセス)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - リンクの中黒は除去されないのでANCHOR_MISSING
        # 正しいリンクは (#マルチユーザー同時アクセス) とすべき
        assert len(results) == 1
        assert results[0].status == LinkStatus.ANCHOR_MISSING.value

    def test_details_tag_id_attribute(self, temp_docs_dir) -> None:
        """<details>タグのid属性が認識されることを確認（lychee互換）"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            '<details id="archive-section">\n<summary>Archive</summary>\n</details>\n\n[Link](#archive-section)',
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_html_id_in_other_elements(self, temp_docs_dir) -> None:
        """任意のHTML要素のid属性が認識される"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            '<div id="custom-anchor"></div>\n\n[Custom](#custom-anchor)',
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_links_in_code_block_skipped(self, temp_docs_dir) -> None:
        """コードブロック内のリンクはスキップされる"""
        # Setup - コードブロック内に意図的に壊れたリンクを含む
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "# Doc\n\n```text\n[broken](./nonexistent.md)\n```\n\n[valid](index.md)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - コードブロック外のリンクのみ検出
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value
        assert results[0].link_target == "index.md"

    def test_links_in_fenced_code_block_with_language(self, temp_docs_dir) -> None:
        """言語指定付きコードブロック内のリンクもスキップされる"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "# Doc\n\n```markdown\n[example](./example.md)\n```\n\n[real](index.md)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].link_target == "index.md"

    def test_links_in_inline_code_span_skipped(self, temp_docs_dir) -> None:
        """インラインコードスパン（`...`）内のリンクはスキップされる"""
        # Setup - バッククォート内にリンク構文がある
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "# Doc\n\nExample: `[link](./broken.md)` is code\n\n[real](index.md)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - インラインコード外のリンクのみ検出
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value
        assert results[0].link_target == "index.md"

    def test_links_in_table_code_span_skipped(self, temp_docs_dir) -> None:
        """テーブル内のインラインコードスパン内リンクもスキップされる"""
        # Setup - SSoTドキュメントのような形式
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "# Doc\n\n| Col1 | Col2 |\n|------|------|\n| info | `[例](../../nonexistent.md)` |\n\n[real](index.md)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify
        assert len(results) == 1
        assert results[0].link_target == "index.md"


class TestCheckSummary:
    """CheckSummary のテスト"""

    def test_summary_to_dict(self) -> None:
        """サマリーの辞書変換"""
        summary = CheckSummary(
            total_files=10,
            total_links=50,
            valid=40,
            broken=5,
            anchor_missing=2,
            external=3,
            skipped=0,
        )

        d = summary.to_dict()

        assert d["total_files"] == 10
        assert d["total_links"] == 50
        assert d["valid"] == 40
        assert d["broken"] == 5


class TestSlugifyLycheeCompat:
    """_slugify メソッドの lychee 互換テスト"""

    def test_emoji_heading_generates_leading_hyphen(self, temp_docs_dir) -> None:
        """絵文字付き見出しは先頭ハイフンを生成（lychee互換）

        lychee/GitHubでは絵文字が削除された後、スペースがハイフンになり、
        先頭のハイフンは保持される。
        例: "## 📥 必須パラメータ" → "-必須パラメータ"
        """
        # Setup - 絵文字付き見出しと、先頭ハイフンなしのリンク
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "## 📥 必須パラメータ\n\n[リンク](#必須パラメータ)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - 絵文字が削除され先頭ハイフンが残るため、リンクは無効
        assert len(results) == 1
        assert results[0].status == LinkStatus.ANCHOR_MISSING.value

    def test_emoji_heading_with_correct_anchor(self, temp_docs_dir) -> None:
        """絵文字付き見出しへの正しいアンカーリンク

        正しいリンクは先頭ハイフンを含む必要がある。
        """
        # Setup - 絵文字付き見出しと、先頭ハイフン付きのリンク
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "## 📥 必須パラメータ\n\n[リンク](#-必須パラメータ)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - 先頭ハイフン付きリンクは有効
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_heading_without_emoji_no_leading_hyphen(self, temp_docs_dir) -> None:
        """絵文字なし見出しは先頭ハイフンなし"""
        # Setup - 絵文字なし見出し
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "## 必須パラメータ\n\n[リンク](#必須パラメータ)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - 絵文字なしなら先頭ハイフンは不要
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_underscore_stripped_from_anchor(self, temp_docs_dir) -> None:
        """アンダースコアはアンカーから除去される（lychee互換）

        GitHubはアンダースコアを保持しないため、link_checkerも同様に振る舞う。
        """
        # Setup - アンダースコア付き見出し
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "## test_section\n\n[リンク](#testsection)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - アンダースコアなしのリンクが有効
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value

    def test_multiple_emojis_in_heading(self, temp_docs_dir) -> None:
        """複数絵文字を含む見出し"""
        # Setup
        file1 = temp_docs_dir / "index.md"
        file1.write_text(
            "## 🚀 ロケット 🌟 スター\n\n[リンク](#-ロケット--スター)",
            encoding="utf-8",
        )

        # Execute
        checker = MarkdownLinkChecker(temp_docs_dir)
        results = checker.check_all()

        # Verify - 絵文字が削除され、スペースがハイフンに、連続ハイフン保持
        assert len(results) == 1
        assert results[0].status == LinkStatus.VALID.value
