#!/usr/bin/env python3
"""
test_check_footer.py
====================

tools/check_footer.py の単体テスト。
フッター解析、チェック、修正機能をテスト。
"""

from pathlib import Path
from typing import List

import pytest

from tools.check_footer import (
    CheckResult,
    FooterDefinition,
    FooterStatus,
    check_footer_in_file,
    fix_footer,
    parse_footer_md,
    run_check,
)

# =============================================================================
# parse_footer_md テスト
# =============================================================================


class TestParseFooterMd:
    """parse_footer_md() 関数のテスト"""

    def test_extract_footer_content(self, tmp_path: Path) -> None:
        """フッター内容を正しく抽出"""
        footer_md = tmp_path / "_footer.md"
        footer_md.write_text(
            """# フッター定義

## フッター内容

```text
---
**Test Footer** | [Link](https://example.com)
```

## 適用ファイル一覧

### test_dir/
- `README.md`
""",
            encoding="utf-8",
        )

        result = parse_footer_md(footer_md)

        assert result.content == "---\n**Test Footer** | [Link](https://example.com)"

    def test_extract_target_files(self, tmp_path: Path) -> None:
        """対象ファイル一覧を正しく抽出"""
        footer_md = tmp_path / "_footer.md"
        footer_md.write_text(
            """# フッター

```text
---
Footer
```

## 適用ファイル一覧

### ルート（plugins-weave/）
- `README.md`
- `README.en.md`

### EpisodicRAG/
- `CONTRIBUTING.md`

### EpisodicRAG/docs/user/
- `GUIDE.md`
- `FAQ.md`
""",
            encoding="utf-8",
        )

        result = parse_footer_md(footer_md)

        assert "README.md" in result.target_files
        assert "README.en.md" in result.target_files
        assert "EpisodicRAG/CONTRIBUTING.md" in result.target_files
        assert "EpisodicRAG/docs/user/GUIDE.md" in result.target_files
        assert "EpisodicRAG/docs/user/FAQ.md" in result.target_files
        assert len(result.target_files) == 5

    def test_file_not_found(self, tmp_path: Path) -> None:
        """_footer.md が存在しない場合"""
        nonexistent = tmp_path / "nonexistent" / "_footer.md"

        with pytest.raises(FileNotFoundError):
            parse_footer_md(nonexistent)

    def test_missing_footer_block(self, tmp_path: Path) -> None:
        """```text ブロックがない場合"""
        footer_md = tmp_path / "_footer.md"
        footer_md.write_text("# No code block here", encoding="utf-8")

        with pytest.raises(ValueError, match="Footer content not found"):
            parse_footer_md(footer_md)


# =============================================================================
# check_footer_in_file テスト
# =============================================================================


class TestCheckFooterInFile:
    """check_footer_in_file() 関数のテスト"""

    EXPECTED_FOOTER = "---\n**Test** | [Link](https://example.com)"

    def test_footer_exists_ok(self, tmp_path: Path) -> None:
        """フッターが正しく存在する場合 → OK"""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            f"""# Title

Content here.

{self.EXPECTED_FOOTER}
""",
            encoding="utf-8",
        )

        status, message = check_footer_in_file(test_file, self.EXPECTED_FOOTER)

        assert status == FooterStatus.OK
        assert message is None

    def test_footer_missing(self, tmp_path: Path) -> None:
        """フッターがない場合 → MISSING"""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            """# Title

Content here.
""",
            encoding="utf-8",
        )

        status, message = check_footer_in_file(test_file, self.EXPECTED_FOOTER)

        assert status == FooterStatus.MISSING
        assert message is not None

    def test_footer_mismatch(self, tmp_path: Path) -> None:
        """フッターが異なる場合 → MISMATCH"""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            """# Title

Content here.

---
**Wrong Footer** | [Wrong](https://wrong.com)
""",
            encoding="utf-8",
        )

        status, message = check_footer_in_file(test_file, self.EXPECTED_FOOTER)

        assert status == FooterStatus.MISMATCH

    def test_file_not_found(self, tmp_path: Path) -> None:
        """ファイルが存在しない場合 → FILE_NOT_FOUND"""
        nonexistent = tmp_path / "nonexistent.md"

        status, message = check_footer_in_file(nonexistent, self.EXPECTED_FOOTER)

        assert status == FooterStatus.FILE_NOT_FOUND


# =============================================================================
# fix_footer テスト
# =============================================================================


class TestFixFooter:
    """fix_footer() 関数のテスト"""

    EXPECTED_FOOTER = "---\n**Test** | [Link](https://example.com)"

    def test_add_missing_footer(self, tmp_path: Path) -> None:
        """フッターがない場合、追加"""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            """# Title

Content here.
""",
            encoding="utf-8",
        )

        result = fix_footer(test_file, self.EXPECTED_FOOTER)

        assert result is True
        content = test_file.read_text(encoding="utf-8")
        assert self.EXPECTED_FOOTER in content
        assert content.endswith(self.EXPECTED_FOOTER + "\n")

    def test_replace_wrong_footer(self, tmp_path: Path) -> None:
        """フッターが異なる場合、置換"""
        test_file = tmp_path / "test.md"
        test_file.write_text(
            """# Title

Content here.

---
**Wrong Footer**
""",
            encoding="utf-8",
        )

        result = fix_footer(test_file, self.EXPECTED_FOOTER)

        assert result is True
        content = test_file.read_text(encoding="utf-8")
        assert "Wrong Footer" not in content
        assert self.EXPECTED_FOOTER in content

    def test_file_not_found(self, tmp_path: Path) -> None:
        """ファイルが存在しない場合 → False"""
        nonexistent = tmp_path / "nonexistent.md"

        result = fix_footer(nonexistent, self.EXPECTED_FOOTER)

        assert result is False


# =============================================================================
# run_check テスト
# =============================================================================


class TestRunCheck:
    """run_check() 関数のテスト"""

    def _create_test_structure(self, tmp_path: Path) -> Path:
        """テスト用のディレクトリ構造を作成"""
        base = tmp_path / "plugins-weave"
        base.mkdir()

        # _footer.md
        footer_md = base / "EpisodicRAG" / "_footer.md"
        footer_md.parent.mkdir(parents=True)
        footer_md.write_text(
            """# Footer

```text
---
**Footer** | [Link](https://example.com)
```

## 適用ファイル一覧

### ルート（plugins-weave/）
- `README.md`

### EpisodicRAG/
- `TEST.md`
""",
            encoding="utf-8",
        )

        return base

    def test_all_ok(self, tmp_path: Path) -> None:
        """全ファイルOKの場合"""
        base = self._create_test_structure(tmp_path)
        footer = "---\n**Footer** | [Link](https://example.com)"

        # 正しいフッター付きファイルを作成
        readme = base / "README.md"
        readme.write_text(f"# README\n\n{footer}\n", encoding="utf-8")

        test_md = base / "EpisodicRAG" / "TEST.md"
        test_md.write_text(f"# TEST\n\n{footer}\n", encoding="utf-8")

        results = run_check(base / "EpisodicRAG" / "_footer.md", base, fix=False, quiet=True)

        ok_count = sum(1 for r in results if r.status == FooterStatus.OK)
        assert ok_count == 2

    def test_mixed_results(self, tmp_path: Path) -> None:
        """OK と MISSING が混在する場合"""
        base = self._create_test_structure(tmp_path)
        footer = "---\n**Footer** | [Link](https://example.com)"

        # 正しいフッター付きファイル
        readme = base / "README.md"
        readme.write_text(f"# README\n\n{footer}\n", encoding="utf-8")

        # フッターなしファイル
        test_md = base / "EpisodicRAG" / "TEST.md"
        test_md.write_text("# TEST\n\nNo footer here.\n", encoding="utf-8")

        results = run_check(base / "EpisodicRAG" / "_footer.md", base, fix=False, quiet=True)

        statuses = {r.status for r in results}
        assert FooterStatus.OK in statuses
        assert FooterStatus.MISSING in statuses

    def test_fix_mode(self, tmp_path: Path) -> None:
        """--fix モードでフッターを自動追加"""
        base = self._create_test_structure(tmp_path)

        # フッターなしファイル
        readme = base / "README.md"
        readme.write_text("# README\n\nNo footer.\n", encoding="utf-8")

        test_md = base / "EpisodicRAG" / "TEST.md"
        test_md.write_text("# TEST\n\nNo footer.\n", encoding="utf-8")

        results = run_check(base / "EpisodicRAG" / "_footer.md", base, fix=True, quiet=True)

        # 修正後は全てOK
        ok_count = sum(1 for r in results if r.status == FooterStatus.OK)
        assert ok_count == 2

        # ファイルにフッターが追加されている
        readme_content = readme.read_text(encoding="utf-8")
        assert "**Footer**" in readme_content


# =============================================================================
# 統合テスト
# =============================================================================


class TestIntegration:
    """統合テスト"""

    @pytest.mark.integration
    def test_actual_footer_md_parseable(self) -> None:
        """実際の _footer.md がパース可能"""
        # 実際の _footer.md のパス
        scripts_path = Path(__file__).parent.parent.parent
        footer_md_path = scripts_path.parent / "_footer.md"

        if not footer_md_path.exists():
            pytest.skip("_footer.md not found in expected location")

        definition = parse_footer_md(footer_md_path)

        # 基本的な検証
        assert definition.content
        assert "---" in definition.content
        assert len(definition.target_files) > 0
