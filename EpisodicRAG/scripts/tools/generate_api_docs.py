#!/usr/bin/env python3
"""
API Reference Auto-generator
============================

API_REFERENCE.md をハイブリッド生成（自動 + 手動セクション維持）

Usage:
    python generate_api_docs.py          # 生成
    python generate_api_docs.py --check  # 差分チェック（CI用）

Features:
    - Python docstring から自動生成
    - 手動セクション（<!-- MANUAL:xxx -->...<!-- /MANUAL:xxx -->）を保持
    - レイヤー別に整理（Domain, Infrastructure, Application, Interfaces）
"""

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class FunctionInfo:
    """関数情報"""
    name: str
    docstring: Optional[str]
    args: List[str]
    returns: Optional[str]
    is_async: bool = False


@dataclass
class ClassInfo:
    """クラス情報"""
    name: str
    docstring: Optional[str]
    methods: List[FunctionInfo] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)


@dataclass
class ModuleInfo:
    """モジュール情報"""
    name: str
    path: Path
    docstring: Optional[str]
    classes: List[ClassInfo] = field(default_factory=list)
    functions: List[FunctionInfo] = field(default_factory=list)


def extract_module_info(file_path: Path) -> Optional[ModuleInfo]:
    """
    Python ファイルからモジュール情報を抽出

    Args:
        file_path: Python ファイルのパス

    Returns:
        ModuleInfo または None（パース失敗時）
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError) as e:
        print(f"Warning: Could not parse {file_path}: {e}", file=sys.stderr)
        return None

    module = ModuleInfo(
        name=file_path.stem,
        path=file_path,
        docstring=ast.get_docstring(tree),
    )

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            class_info = ClassInfo(
                name=node.name,
                docstring=ast.get_docstring(node),
                bases=[_get_name(base) for base in node.bases],
            )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not item.name.startswith("_") or item.name in ("__init__", "__call__"):
                        func_info = _extract_function_info(item)
                        class_info.methods.append(func_info)
            module.classes.append(class_info)

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                func_info = _extract_function_info(node)
                module.functions.append(func_info)

    return module


def _get_name(node: ast.AST) -> str:
    """AST ノードから名前を取得"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Attribute):
        return f"{_get_name(node.value)}.{node.attr}"
    return "Unknown"


def _extract_function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:
    """関数情報を抽出"""
    args = []
    for arg in node.args.args:
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {_annotation_to_str(arg.annotation)}"
        args.append(arg_str)

    returns = None
    if node.returns:
        returns = _annotation_to_str(node.returns)

    return FunctionInfo(
        name=node.name,
        docstring=ast.get_docstring(node),
        args=args,
        returns=returns,
        is_async=isinstance(node, ast.AsyncFunctionDef),
    )


def _annotation_to_str(node: ast.AST) -> str:
    """型アノテーションを文字列に変換"""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return repr(node.value)
    elif isinstance(node, ast.Subscript):
        return f"{_annotation_to_str(node.value)}[{_annotation_to_str(node.slice)}]"
    elif isinstance(node, ast.Tuple):
        return ", ".join(_annotation_to_str(e) for e in node.elts)
    elif isinstance(node, ast.Attribute):
        return f"{_annotation_to_str(node.value)}.{node.attr}"
    elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
        return f"{_annotation_to_str(node.left)} | {_annotation_to_str(node.right)}"
    return "Any"


def load_manual_sections(api_ref_path: Path) -> Dict[str, str]:
    """
    既存の API_REFERENCE.md から手動セクションを抽出

    Args:
        api_ref_path: API_REFERENCE.md のパス

    Returns:
        セクション名 -> コンテンツのマッピング
    """
    if not api_ref_path.exists():
        return {}

    content = api_ref_path.read_text(encoding="utf-8")
    pattern = r"<!-- MANUAL:(\w+) -->\n(.*?)<!-- /MANUAL:\1 -->"
    matches = re.findall(pattern, content, re.DOTALL)
    return {name: content.strip() for name, content in matches}


def generate_module_markdown(module: ModuleInfo) -> str:
    """モジュールの Markdown を生成"""
    lines = []
    lines.append(f"### {module.name}.py")
    lines.append("")

    if module.docstring:
        # 最初の行のみ使用
        first_line = module.docstring.split("\n")[0].strip()
        if first_line:
            lines.append(f"*{first_line}*")
            lines.append("")

    # クラス
    for cls in module.classes:
        lines.append(f"#### class `{cls.name}`")
        if cls.bases:
            lines.append(f"*Inherits: {', '.join(cls.bases)}*")
        lines.append("")
        if cls.docstring:
            first_line = cls.docstring.split("\n")[0].strip()
            lines.append(f"> {first_line}")
            lines.append("")

        if cls.methods:
            lines.append("| Method | Description |")
            lines.append("|--------|-------------|")
            for method in cls.methods:
                desc = ""
                if method.docstring:
                    desc = method.docstring.split("\n")[0].strip()[:60]
                lines.append(f"| `{method.name}()` | {desc} |")
            lines.append("")

    # モジュールレベル関数
    if module.functions:
        lines.append("#### Functions")
        lines.append("")
        lines.append("| Function | Description |")
        lines.append("|----------|-------------|")
        for func in module.functions:
            desc = ""
            if func.docstring:
                desc = func.docstring.split("\n")[0].strip()[:60]
            lines.append(f"| `{func.name}()` | {desc} |")
        lines.append("")

    return "\n".join(lines)


def scan_layer(layer_path: Path) -> List[ModuleInfo]:
    """レイヤーディレクトリをスキャンしてモジュール情報を収集"""
    modules = []
    if not layer_path.exists():
        return modules

    for py_file in sorted(layer_path.glob("*.py")):
        if py_file.name.startswith("_") and py_file.name != "__init__.py":
            continue
        if py_file.name == "__init__.py":
            continue  # __init__.py はスキップ

        module_info = extract_module_info(py_file)
        if module_info:
            modules.append(module_info)

    return modules


def generate_api_reference(scripts_path: Path, manual_sections: Dict[str, str]) -> str:
    """
    API_REFERENCE.md のコンテンツを生成

    Args:
        scripts_path: scripts ディレクトリのパス
        manual_sections: 保持する手動セクション

    Returns:
        生成された Markdown コンテンツ
    """
    lines = []
    now = datetime.now().strftime("%Y-%m-%d")

    # ヘッダー
    lines.append("# API Reference")
    lines.append("")
    lines.append(f"> Auto-generated: {now} | Manual sections preserved")
    lines.append("")
    lines.append("---")
    lines.append("")

    # レイヤー定義
    layers = [
        ("Domain Layer", scripts_path / "domain"),
        ("Infrastructure Layer", scripts_path / "infrastructure"),
        ("Application Layer", scripts_path / "application"),
        ("Config Layer", scripts_path / "config"),
        ("Interfaces Layer", scripts_path / "interfaces"),
    ]

    for layer_name, layer_path in layers:
        modules = scan_layer(layer_path)
        if not modules:
            continue

        lines.append(f"## {layer_name}")
        lines.append("")

        for module in modules:
            lines.append(generate_module_markdown(module))

        lines.append("---")
        lines.append("")

    # 手動セクションを追加
    for section_name, content in manual_sections.items():
        lines.append(f"<!-- MANUAL:{section_name} -->")
        lines.append(content)
        lines.append(f"<!-- /MANUAL:{section_name} -->")
        lines.append("")

    # デフォルトの手動セクション（存在しない場合）
    default_sections = ["workflow_diagrams", "examples", "configuration", "error_recovery"]
    for section in default_sections:
        if section not in manual_sections:
            lines.append(f"<!-- MANUAL:{section} -->")
            lines.append(f"## {section.replace('_', ' ').title()} (Manual)")
            lines.append("")
            lines.append("*このセクションは手動で編集してください*")
            lines.append("")
            lines.append(f"<!-- /MANUAL:{section} -->")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate API_REFERENCE.md from docstrings")
    parser.add_argument("--check", action="store_true", help="Check if docs are up to date")
    parser.add_argument("--output", type=Path, help="Output file path")
    args = parser.parse_args()

    # パス設定
    scripts_path = Path(__file__).parent.parent
    docs_path = scripts_path.parent / "docs" / "dev"
    api_ref_path = docs_path / "API_REFERENCE.md"

    if args.output:
        api_ref_path = args.output

    # 手動セクションを読み込み
    manual_sections = load_manual_sections(api_ref_path)

    # 生成
    content = generate_api_reference(scripts_path, manual_sections)

    if args.check:
        # 差分チェック
        if api_ref_path.exists():
            existing = api_ref_path.read_text(encoding="utf-8")
            if existing.strip() == content.strip():
                print("API_REFERENCE.md is up to date.")
                sys.exit(0)
            else:
                print("API_REFERENCE.md is out of date. Run 'python generate_api_docs.py' to update.")
                sys.exit(1)
        else:
            print("API_REFERENCE.md does not exist.")
            sys.exit(1)
    else:
        # 書き込み
        docs_path.mkdir(parents=True, exist_ok=True)
        api_ref_path.write_text(content, encoding="utf-8")
        print(f"Generated: {api_ref_path}")


if __name__ == "__main__":
    main()
