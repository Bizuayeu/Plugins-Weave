# frameworks/templates/__init__.py
"""
テンプレートシステム

簡易テンプレートエンジンを提供する。
インメモリキャッシュにより、ディスクI/Oを削減。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from domain.exceptions import TemplateError

# テンプレートキャッシュ（モジュールレベル）
_template_cache: dict[str, str] = {}


def get_templates_dir() -> str:
    """テンプレートディレクトリのパスを取得"""
    return str(Path(__file__).parent)


def load_template(name: str, use_cache: bool = True) -> str:
    """
    テンプレートファイルをロードする（キャッシュ付き）。

    Args:
        name: テンプレートファイル名
        use_cache: キャッシュを使用するか（デフォルトTrue）

    Returns:
        テンプレートの内容

    Raises:
        TemplateError: ファイルが存在しない場合
    """
    # キャッシュ確認
    if use_cache and name in _template_cache:
        return _template_cache[name]

    template_path = Path(get_templates_dir()) / name
    if not template_path.exists():
        raise TemplateError(f"Template not found: {name}")

    with open(template_path, encoding="utf-8") as f:
        content = f.read()

    # キャッシュに保存
    if use_cache:
        _template_cache[name] = content

    return content


def clear_template_cache() -> None:
    """テンプレートキャッシュをクリアする（テスト用）"""
    _template_cache.clear()


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
    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in kwargs:
            return str(kwargs[key])
        # group(0) は常にマッチした全体を返すので None にならない
        return str(match.group(0))

    return re.sub(r'\{\{(\w+)\}\}', replacer, template)


__all__ = ["TemplateError", "clear_template_cache", "load_template", "render_template"]
