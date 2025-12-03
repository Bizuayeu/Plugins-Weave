#!/usr/bin/env python3
"""
Footer Consistency Checker
==========================

_footer.md で定義されたフッターが各ドキュメントに正しく適用されているかをチェック。

Usage:
    python -m tools.check_footer          # チェック実行
    python -m tools.check_footer --fix    # 不足しているフッターを自動追加
    python -m tools.check_footer --quiet  # サマリーのみ出力

Features:
    - _footer.md からフッター定義を読み込み
    - 適用対象ファイル一覧を自動抽出
    - OK / MISSING / MISMATCH を分類
    - --fix オプションで自動修正
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


class FooterStatus(Enum):
    """フッターの状態"""

    OK = "OK"
    MISSING = "MISSING"
    MISMATCH = "MISMATCH"
    FILE_NOT_FOUND = "FILE_NOT_FOUND"


@dataclass
class FooterDefinition:
    """フッター定義"""

    content: str
    target_files: List[str] = field(default_factory=list)


@dataclass
class CheckResult:
    """チェック結果"""

    file_path: Path
    status: FooterStatus
    message: Optional[str] = None


def parse_footer_md(footer_md_path: Path) -> FooterDefinition:
    """
    _footer.md からフッター定義を解析

    Args:
        footer_md_path: _footer.md のパス

    Returns:
        FooterDefinition（フッター内容と対象ファイル一覧）

    Raises:
        ValueError: フッター定義が見つからない場合
    """
    if not footer_md_path.exists():
        raise FileNotFoundError(f"_footer.md not found: {footer_md_path}")

    content = footer_md_path.read_text(encoding="utf-8")

    # フッター内容を抽出（```text ... ``` ブロック）
    footer_match = re.search(r"```text\n(.*?)\n```", content, re.DOTALL)
    if not footer_match:
        raise ValueError("Footer content not found in _footer.md (expected ```text ... ``` block)")

    footer_content = footer_match.group(1).strip()

    # 対象ファイル一覧を抽出（- `filename` 形式）
    target_files = []
    current_section = None

    for line in content.split("\n"):
        # セクションヘッダー（### で始まる行）
        section_match = re.match(r"^###\s+(.+)", line)
        if section_match:
            current_section = section_match.group(1).strip()
            # パス部分を抽出
            # "ルート（plugins-weave/）" や "root (plugins-weave/)" のようなケース
            path_match = re.search(r"[（(]([^）)]+)[）)]", current_section)
            if path_match:
                current_section = path_match.group(1).rstrip("/")
            elif current_section.endswith("/"):
                # "EpisodicRAG/docs/user/" → "EpisodicRAG/docs/user"
                current_section = current_section[:-1]
            continue

        # ファイルエントリ（- `filename` 形式）
        file_match = re.match(r"^-\s+`([^`]+)`", line)
        if file_match and current_section:
            filename = file_match.group(1)
            # セクションパスとファイル名を結合
            if current_section == "plugins-weave":
                # ルートセクションの場合
                target_files.append(filename)
            else:
                target_files.append(f"{current_section}/{filename}")

    return FooterDefinition(content=footer_content, target_files=target_files)


def check_footer_in_file(
    file_path: Path, expected_footer: str
) -> Tuple[FooterStatus, Optional[str]]:
    """
    ファイル内のフッターをチェック

    Args:
        file_path: チェック対象ファイルのパス
        expected_footer: 期待されるフッター内容

    Returns:
        (ステータス, メッセージ) のタプル
    """
    if not file_path.exists():
        return FooterStatus.FILE_NOT_FOUND, f"File not found: {file_path}"

    content = file_path.read_text(encoding="utf-8")

    # 末尾の空白行を除去してチェック
    lines = content.rstrip().split("\n")

    # 期待されるフッターの行
    expected_lines = expected_footer.strip().split("\n")

    # 末尾N行を取得
    n = len(expected_lines)
    if len(lines) < n:
        return FooterStatus.MISSING, "File too short to contain footer"

    actual_footer_lines = lines[-n:]

    # 完全一致チェック
    if actual_footer_lines == expected_lines:
        return FooterStatus.OK, None

    # フッターが存在するが内容が異なる場合
    # "---" で始まる行があればフッターらしきものが存在
    for i, line in enumerate(reversed(lines)):
        if i >= 5:  # 末尾5行以内を探索
            break
        if line.strip() == "---":
            return FooterStatus.MISMATCH, "Footer exists but content differs"

    return FooterStatus.MISSING, "Footer not found"


def fix_footer(file_path: Path, expected_footer: str) -> bool:
    """
    フッターを修正（追加または置換）

    Args:
        file_path: 対象ファイルのパス
        expected_footer: 期待されるフッター内容

    Returns:
        修正が行われた場合 True
    """
    if not file_path.exists():
        return False

    content = file_path.read_text(encoding="utf-8")

    # 末尾の空白行を除去
    content = content.rstrip()

    # 既存のフッター（---で始まる最後のブロック）を除去
    lines = content.split("\n")
    footer_start = None

    for i in range(len(lines) - 1, max(len(lines) - 10, -1), -1):
        if lines[i].strip() == "---":
            footer_start = i
            break

    if footer_start is not None:
        # 既存フッターを除去
        lines = lines[:footer_start]
        content = "\n".join(lines).rstrip()

    # 新しいフッターを追加
    new_content = content + "\n\n" + expected_footer + "\n"
    file_path.write_text(new_content, encoding="utf-8")

    return True


def run_check(
    footer_md_path: Path, base_path: Path, fix: bool = False, quiet: bool = False
) -> List[CheckResult]:
    """
    フッターチェックを実行

    Args:
        footer_md_path: _footer.md のパス
        base_path: 対象ファイルのベースパス
        fix: True の場合、問題を自動修正
        quiet: True の場合、サマリーのみ出力

    Returns:
        チェック結果のリスト
    """
    definition = parse_footer_md(footer_md_path)
    results: List[CheckResult] = []

    for relative_path in definition.target_files:
        file_path = base_path / relative_path
        status, message = check_footer_in_file(file_path, definition.content)

        if fix and status in (FooterStatus.MISSING, FooterStatus.MISMATCH):
            if fix_footer(file_path, definition.content):
                message = "Fixed"
                status = FooterStatus.OK

        results.append(CheckResult(file_path=file_path, status=status, message=message))

    return results


def print_report(results: List[CheckResult], quiet: bool = False) -> None:
    """
    レポートを出力

    Args:
        results: チェック結果のリスト
        quiet: True の場合、サマリーのみ出力
    """
    if not quiet:
        print("Footer Check Report")
        print("=" * 40)
        print()

        for result in results:
            # 相対パスで表示
            rel_path = result.file_path.name
            if result.file_path.parent.name:
                rel_path = f"{result.file_path.parent.name}/{rel_path}"

            if result.status == FooterStatus.OK:
                print(f"  OK: {rel_path}")
            elif result.status == FooterStatus.MISSING:
                print(f"  MISSING: {rel_path}")
            elif result.status == FooterStatus.MISMATCH:
                print(f"  MISMATCH: {rel_path}")
            elif result.status == FooterStatus.FILE_NOT_FOUND:
                print(f"  NOT_FOUND: {rel_path}")

        print()

    # サマリー
    ok_count = sum(1 for r in results if r.status == FooterStatus.OK)
    issue_count = len(results) - ok_count

    print(f"Summary: {ok_count}/{len(results)} files OK", end="")
    if issue_count > 0:
        print(f", {issue_count} issues found")
    else:
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check footer consistency across documentation files"
    )
    parser.add_argument("--fix", action="store_true", help="Auto-fix missing or mismatched footers")
    parser.add_argument("--quiet", action="store_true", help="Only print summary")
    args = parser.parse_args()

    # パス設定
    scripts_path = Path(__file__).parent.parent
    episodic_rag_path = scripts_path.parent
    footer_md_path = episodic_rag_path / "_footer.md"
    base_path = episodic_rag_path.parent  # plugins-weave/

    try:
        results = run_check(footer_md_path, base_path, fix=args.fix, quiet=args.quiet)
        print_report(results, quiet=args.quiet)

        # 問題があれば終了コード1
        has_issues = any(r.status != FooterStatus.OK for r in results)
        sys.exit(1 if has_issues else 0)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
