# frameworks/templates/__init__.py
"""
テンプレートシステム

簡易テンプレートエンジンを提供する。
"""
from __future__ import annotations

import os
import re
from typing import Any


class TemplateError(Exception):
    """テンプレート処理エラー"""
    pass


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

    Args:
        template: テンプレート文字列
        **kwargs: 置換する値

    Returns:
        レンダリングされた文字列
    """
    result = template
    for key, value in kwargs.items():
        placeholder = "{{" + key + "}}"
        result = result.replace(placeholder, str(value))
    return result


__all__ = ["load_template", "render_template", "TemplateError"]
