"""ZipPackagerのテスト(TDD)"""
import contextlib
import logging
from pathlib import Path

import pytest

from adapters.zip_packager import ZipPackager


@pytest.fixture
def packager(tmp_path):
    """テスト用ZipPackagerインスタンス"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return ZipPackager(str(output_dir))


class TestZipPackagerLogging:
    """ログ出力のテスト"""

    def test_logs_warning_for_missing_file(self, packager, caplog):
        """存在しないファイルでwarningログが出ること"""
        with caplog.at_level(logging.WARNING), contextlib.suppress(Exception):
            packager.create_skill_zip(
                skill_md_path=Path("/nonexistent/SKILL.md"),
                html_path=Path("/nonexistent/UI.html"),
                template_path=Path("/nonexistent/template.html"),
                json_path=Path("/nonexistent/images.json"),
            )

        # ログにファイルが見つからない旨が記録されていること
        assert "not found" in caplog.text.lower() or "missing" in caplog.text.lower(), \
            "存在しないファイルに対するwarningログが出力されるべき"

    def test_strict_mode_raises_for_missing_required(self, packager):
        """strict=TrueでFileNotFoundErrorが発生すること"""
        with pytest.raises(FileNotFoundError):
            packager.create_skill_zip(
                skill_md_path=Path("/nonexistent/SKILL.md"),
                html_path=Path("/nonexistent/UI.html"),
                template_path=Path("/nonexistent/template.html"),
                json_path=Path("/nonexistent/images.json"),
                strict=True,
            )

    def test_strict_false_does_not_raise(self, packager):
        """strict=False（デフォルト）では例外が発生しないこと"""
        # 例外が発生しないことを確認
        result = packager.create_skill_zip(
            skill_md_path=Path("/nonexistent/SKILL.md"),
            html_path=Path("/nonexistent/UI.html"),
            template_path=Path("/nonexistent/template.html"),
            json_path=Path("/nonexistent/images.json"),
        )
        assert result is not None
