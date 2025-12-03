#!/usr/bin/env python3
"""
Markdown Link Checker
=====================

Markdownファイル内のリンクを検証するツール。

Usage:
    python -m tools.link_checker [docs_path]           # 検証実行
    python -m tools.link_checker [docs_path] --verbose # 詳細出力
    python -m tools.link_checker [docs_path] --json    # JSON出力

Features:
    1. 相対リンクの有効性検証 [text](path/to/file.md)
    2. アンカーリンクの検証 [text](#section-name)
    3. ファイル+アンカーの複合検証 [text](file.md#section)
    4. 外部リンクの検出（検証はスキップ）
    5. 検証結果のサマリー出力
"""

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set


class LinkStatus(Enum):
    """リンクの状態"""

    VALID = "valid"
    BROKEN = "broken"
    ANCHOR_MISSING = "anchor_missing"
    EXTERNAL = "external"  # 外部リンク（検証スキップ）
    SKIPPED = "skipped"  # 検証対象外


@dataclass
class LinkCheckResult:
    """リンク検証結果"""

    file_path: str
    line_number: int
    link_text: str
    link_target: str
    status: str
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return asdict(self)


@dataclass
class CheckSummary:
    """検証結果サマリー"""

    total_files: int = 0
    total_links: int = 0
    valid: int = 0
    broken: int = 0
    anchor_missing: int = 0
    external: int = 0
    skipped: int = 0

    def to_dict(self) -> Dict:
        """辞書形式に変換"""
        return asdict(self)


class MarkdownLinkChecker:
    """Markdownファイルのリンク検証"""

    # Markdownリンクパターン: [text](url)
    LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")

    # 外部リンクパターン
    EXTERNAL_PATTERN = re.compile(r"^https?://", re.IGNORECASE)

    # アンカーのみパターン
    ANCHOR_ONLY_PATTERN = re.compile(r"^#[\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF-]+$")

    def __init__(self, docs_root: Path):
        """
        Args:
            docs_root: ドキュメントルートディレクトリ
        """
        self.docs_root = docs_root.resolve()
        self.results: List[LinkCheckResult] = []
        self._heading_cache: Dict[Path, Set[str]] = {}

    def check_all(self) -> List[LinkCheckResult]:
        """
        全.mdファイルを検証

        Returns:
            検証結果のリスト
        """
        self.results = []

        if not self.docs_root.exists():
            return self.results

        for md_file in self.docs_root.rglob("*.md"):
            self.check_file(md_file)

        return self.results

    def check_file(self, file_path: Path) -> List[LinkCheckResult]:
        """
        単一ファイルを検証

        Args:
            file_path: 検証対象ファイル

        Returns:
            検証結果のリスト
        """
        file_results: List[LinkCheckResult] = []

        if not file_path.exists():
            return file_results

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return file_results

        lines = content.split("\n")

        for line_num, line in enumerate(lines, start=1):
            for match in self.LINK_PATTERN.finditer(line):
                link_text = match.group(1)
                link_target = match.group(2)

                result = self._validate_link(file_path, line_num, link_text, link_target)
                file_results.append(result)
                self.results.append(result)

        return file_results

    def _validate_link(
        self, source_file: Path, line_num: int, link_text: str, link_target: str
    ) -> LinkCheckResult:
        """
        リンクを検証

        Args:
            source_file: リンク元ファイル
            line_num: 行番号
            link_text: リンクテキスト
            link_target: リンク先

        Returns:
            検証結果
        """
        rel_path = str(source_file.relative_to(self.docs_root))

        # 外部リンク
        if self.EXTERNAL_PATTERN.match(link_target):
            return LinkCheckResult(
                file_path=rel_path,
                line_number=line_num,
                link_text=link_text,
                link_target=link_target,
                status=LinkStatus.EXTERNAL.value,
            )

        # アンカーのみ（同一ファイル内）
        if link_target.startswith("#"):
            anchor = link_target[1:]
            if self._validate_anchor(source_file, anchor):
                return LinkCheckResult(
                    file_path=rel_path,
                    line_number=line_num,
                    link_text=link_text,
                    link_target=link_target,
                    status=LinkStatus.VALID.value,
                )
            else:
                return LinkCheckResult(
                    file_path=rel_path,
                    line_number=line_num,
                    link_text=link_text,
                    link_target=link_target,
                    status=LinkStatus.ANCHOR_MISSING.value,
                    suggestion=f"Anchor '{anchor}' not found in current file",
                )

        # ファイル参照（アンカー付きの場合もあり）
        if "#" in link_target:
            file_part, anchor = link_target.split("#", 1)
        else:
            file_part = link_target
            anchor = None

        # ファイルパス解決
        target_path = self._resolve_path(source_file, file_part)

        if target_path is None or not target_path.exists():
            suggestion = self._suggest_correction(source_file, file_part)
            return LinkCheckResult(
                file_path=rel_path,
                line_number=line_num,
                link_text=link_text,
                link_target=link_target,
                status=LinkStatus.BROKEN.value,
                suggestion=suggestion,
            )

        # アンカーの検証（存在する場合）
        if anchor:
            if not self._validate_anchor(target_path, anchor):
                return LinkCheckResult(
                    file_path=rel_path,
                    line_number=line_num,
                    link_text=link_text,
                    link_target=link_target,
                    status=LinkStatus.ANCHOR_MISSING.value,
                    suggestion=f"Anchor '{anchor}' not found in {file_part}",
                )

        return LinkCheckResult(
            file_path=rel_path,
            line_number=line_num,
            link_text=link_text,
            link_target=link_target,
            status=LinkStatus.VALID.value,
        )

    def _resolve_path(self, source_file: Path, target: str) -> Optional[Path]:
        """
        相対パスを解決

        Args:
            source_file: リンク元ファイル
            target: リンク先パス

        Returns:
            解決されたパス、または None
        """
        if not target:
            return None

        # URL エンコードされたパスをデコード
        target = target.replace("%20", " ")

        # 相対パスの解決
        resolved = (source_file.parent / target).resolve()

        # docs_root外へのアクセスは許可（プロジェクト内の他ファイル参照）
        return resolved

    def _validate_anchor(self, file_path: Path, anchor: str) -> bool:
        """
        アンカー（見出し）の存在確認

        Args:
            file_path: 対象ファイル
            anchor: アンカー名

        Returns:
            存在すれば True
        """
        headings = self._get_headings(file_path)
        return anchor.lower() in headings

    def _get_headings(self, file_path: Path) -> Set[str]:
        """
        ファイル内の見出しを取得（キャッシュ付き）

        Args:
            file_path: 対象ファイル

        Returns:
            見出しのセット（小文字、スラッグ化済み）
        """
        if file_path in self._heading_cache:
            return self._heading_cache[file_path]

        headings: Set[str] = set()

        if not file_path.exists():
            return headings

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return headings

        # Markdown見出しパターン: # Heading
        heading_pattern = re.compile(r"^#+\s+(.+)$", re.MULTILINE)

        for match in heading_pattern.finditer(content):
            heading_text = match.group(1).strip()
            slug = self._slugify(heading_text)
            headings.add(slug)

        self._heading_cache[file_path] = headings
        return headings

    def _slugify(self, text: str) -> str:
        """
        見出しテキストをスラッグ化（GitHub風）

        Args:
            text: 見出しテキスト

        Returns:
            スラッグ化されたテキスト
        """
        # 小文字化
        slug = text.lower()

        # 特殊文字を除去（日本語は保持）
        slug = re.sub(r"[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\s-]", "", slug)

        # スペースをハイフンに（各スペースを個別に置換、GitHubと同じ動作）
        slug = re.sub(r"\s", "-", slug)

        # Note: GitHubは連続ハイフンを保持するため、折りたたみは行わない
        # slug = re.sub(r"-+", "-", slug)

        # 先頭・末尾のハイフンを除去
        slug = slug.strip("-")

        return slug

    def _suggest_correction(self, source_file: Path, broken_target: str) -> Optional[str]:
        """
        壊れたリンクの修正案を提案

        Args:
            source_file: リンク元ファイル
            broken_target: 壊れたリンク先

        Returns:
            修正案、または None
        """
        # 同じディレクトリ内で類似ファイルを検索
        target_name = Path(broken_target).name
        parent_dir = source_file.parent

        if parent_dir.exists():
            for f in parent_dir.glob("*.md"):
                if f.name.lower() == target_name.lower() and f.name != target_name:
                    return f"Did you mean '{f.name}'?"

        return f"File not found: {broken_target}"

    def get_summary(self) -> CheckSummary:
        """
        検証結果サマリーを取得

        Returns:
            CheckSummary
        """
        summary = CheckSummary()

        files_seen: Set[str] = set()

        for result in self.results:
            files_seen.add(result.file_path)
            summary.total_links += 1

            if result.status == LinkStatus.VALID.value:
                summary.valid += 1
            elif result.status == LinkStatus.BROKEN.value:
                summary.broken += 1
            elif result.status == LinkStatus.ANCHOR_MISSING.value:
                summary.anchor_missing += 1
            elif result.status == LinkStatus.EXTERNAL.value:
                summary.external += 1
            elif result.status == LinkStatus.SKIPPED.value:
                summary.skipped += 1

        summary.total_files = len(files_seen)
        return summary

    def get_broken_links(self) -> List[LinkCheckResult]:
        """
        壊れたリンクのみを取得

        Returns:
            壊れたリンクのリスト
        """
        return [
            r
            for r in self.results
            if r.status in (LinkStatus.BROKEN.value, LinkStatus.ANCHOR_MISSING.value)
        ]


def main():
    """CLIエントリーポイント"""
    # Windows環境でのUnicode出力対応
    import io

    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Markdown Link Checker - ドキュメント内リンクの検証",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m tools.link_checker ../docs
    python -m tools.link_checker ../docs --verbose
    python -m tools.link_checker ../docs --json > results.json
        """,
    )

    parser.add_argument(
        "docs_path",
        type=Path,
        nargs="?",
        default=Path(__file__).parent.parent.parent / "docs",
        help="ドキュメントルートディレクトリ（デフォルト: ../docs）",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="詳細出力（全リンクを表示）",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON形式で出力",
    )

    parser.add_argument(
        "--errors-only",
        "-e",
        action="store_true",
        help="エラーのみ表示",
    )

    args = parser.parse_args()

    # パス解決
    docs_path = args.docs_path.resolve()

    if not docs_path.exists():
        print(f"Error: Directory not found: {docs_path}", file=sys.stderr)
        sys.exit(1)

    # 検証実行
    checker = MarkdownLinkChecker(docs_path)
    checker.check_all()

    summary = checker.get_summary()
    broken = checker.get_broken_links()

    # JSON出力
    if args.json:
        output = {
            "summary": summary.to_dict(),
            "broken_links": [r.to_dict() for r in broken],
        }
        if args.verbose:
            output["all_links"] = [r.to_dict() for r in checker.results]
        print(json.dumps(output, indent=2, ensure_ascii=False))
        sys.exit(0 if not broken else 1)

    # テキスト出力
    print(f"\n{'=' * 60}")
    print("Markdown Link Checker Results")
    print(f"{'=' * 60}")
    print(f"Directory: {docs_path}")
    print(f"Files checked: {summary.total_files}")
    print(f"Total links: {summary.total_links}")
    print(f"{'=' * 60}")
    print(f"  Valid:          {summary.valid}")
    print(f"  Broken:         {summary.broken}")
    print(f"  Anchor missing: {summary.anchor_missing}")
    print(f"  External:       {summary.external}")
    print(f"{'=' * 60}")

    # 詳細出力
    if args.verbose and not args.errors_only:
        print("\nAll links:")
        for result in checker.results:
            status_icon = {
                LinkStatus.VALID.value: "[OK]",
                LinkStatus.BROKEN.value: "[BROKEN]",
                LinkStatus.ANCHOR_MISSING.value: "[ANCHOR?]",
                LinkStatus.EXTERNAL.value: "[EXT]",
            }.get(result.status, "[?]")
            print(f"  {status_icon} {result.file_path}:{result.line_number}")
            print(f"         {result.link_target}")

    # エラー詳細
    if broken:
        print("\nBroken links:")
        for result in broken:
            print(f"  {result.file_path}:{result.line_number}")
            print(f"    Link: [{result.link_text}]({result.link_target})")
            if result.suggestion:
                print(f"    Hint: {result.suggestion}")
            print()

    # 終了コード
    if broken:
        print(f"\nFound {len(broken)} broken link(s).")
        sys.exit(1)
    else:
        print("\nAll links are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()
