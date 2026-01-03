"""インポート構造のテスト（TDD）"""

from pathlib import Path


def test_relative_import_works():
    """相対インポートが機能すること"""
    from usecases.base64_encoder import Base64Encoder
    from usecases.html_builder import HtmlBuilder
    from usecases.image_splitter import ImageSplitter

    assert ImageSplitter is not None
    assert Base64Encoder is not None
    assert HtmlBuilder is not None


def test_no_try_except_in_source():
    """ソースコードにtry/exceptインポートがないこと"""
    usecases_dir = Path(__file__).parent.parent / "usecases"

    for py_file in usecases_dir.glob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        assert "except ImportError:" not in content, (
            f"{py_file.name}にtry/exceptインポートが残っている"
        )
