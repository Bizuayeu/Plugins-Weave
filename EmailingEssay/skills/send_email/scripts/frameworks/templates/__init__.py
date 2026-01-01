# frameworks/templates/__init__.py
"""
テンプレートシステム

簡易テンプレートエンジンを提供する。
TemplateError は domain.exceptions に移動済み。
"""
from __future__ import annotations

import os
import re
from typing import Any

from domain.exceptions import TemplateError


def get_templates_dir() -> str:
    """テンプレートディレクトリのパスを取得"""
    return os.path.dirname(os.path.abspath(__file__))


def load_template(name: str) -> str:
    """
    テンプレートファイルをロードする。

    Args:
        name: テンプレートファイル名

    Returns:
        テンプレートの内容

    Raises:
        TemplateError: ファイルが存在しない場合
    """
    template_path = os.path.join(get_templates_dir(), name)
    if not os.path.exists(template_path):
        raise TemplateError(f"Template not found: {name}")

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def render_template(template: str, **kwargs: Any) -> str:
    """
    テンプレートをレンダリングする。

    {{key}} 形式のプレースホルダーを置換する。
    二重置換を防ぐため、一度に全てのプレースホルダーを特定してから置換する。

    Args:
        template: テンプレート文字列
        **kwargs: 置換する値

    Returns:
        レンダリングされた文字列
    """
    # 正規表現で全プレースホルダーを特定し、一度に置換
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in kwargs:
            return str(kwargs[key])
        return match.group(0)  # マッチしない場合は元のプレースホルダーを保持

    return re.sub(r'\{\{(\w+)\}\}', replacer, template)


__all__ = ["load_template", "render_template", "TemplateError"]
