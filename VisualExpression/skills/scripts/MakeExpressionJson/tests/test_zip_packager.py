"""ZipPackagerのテスト(TDD)"""

import contextlib
import logging
from pathlib import Path

import pytest

from adapters.zip_packager import ZipPackager


class TestZipPackagerDirectoryCreation:
    """ZipPackager のディレクトリ作成テスト（TDD）"""

    def test_create_skill_zip_creates_output_dir(self, tmp_path):
        """create_skill_zip が出力ディレクトリを自動作成すること"""
        output_dir = tmp_path / "nonexistent" / "nested"
        packager = ZipPackager(str(output_dir))

        # strict=False で missing file エラーを回避
        packager.create_skill_zip(
            skill_md_path=Path("/dummy"),
            html_path=Path("/dummy"),
            template_path=Path("/dummy"),
            json_path=Path("/dummy"),
            strict=False,
        )

        assert output_dir.exists()

    def test_create_minimal_zip_creates_output_dir(self, tmp_path):
        """create_minimal_zip が出力ディレクトリを自動作成すること"""
        output_dir = tmp_path / "another" / "nested"
        packager = ZipPackager(str(output_dir))

        packager.create_minimal_zip(html_path=Path("/dummy"))

        assert output_dir.exists()


@pytest.fixture
def packager(tmp_path):
    """テスト用ZipPackagerインスタンス"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return ZipPackager(str(output_dir))


class TestZipPackagerStrictDefault:
    """strict パラメータのデフォルト値テスト"""

    def test_strict_default_is_true(self):
        """strict パラメータのデフォルトが True であることを確認"""
        import inspect

        sig = inspect.signature(ZipPackager.create_skill_zip)
        assert sig.parameters["strict"].default is True


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
                strict=False,  # 明示的にFalseを指定
            )

        # ログにファイルが見つからない旨が記録されていること
        assert "not found" in caplog.text.lower() or "missing" in caplog.text.lower(), (
            "存在しないファイルに対するwarningログが出力されるべき"
        )

    def test_strict_mode_raises_for_missing_required(self, packager):
        """strict=True（デフォルト）でFileNotFoundErrorが発生すること"""
        with pytest.raises(FileNotFoundError):
            packager.create_skill_zip(
                skill_md_path=Path("/nonexistent/SKILL.md"),
                html_path=Path("/nonexistent/UI.html"),
                template_path=Path("/nonexistent/template.html"),
                json_path=Path("/nonexistent/images.json"),
                # strict=True is now the default
            )

    def test_strict_false_does_not_raise(self, packager):
        """strict=False では例外が発生しないこと"""
        # 例外が発生しないことを確認
        result = packager.create_skill_zip(
            skill_md_path=Path("/nonexistent/SKILL.md"),
            html_path=Path("/nonexistent/UI.html"),
            template_path=Path("/nonexistent/template.html"),
            json_path=Path("/nonexistent/images.json"),
            strict=False,  # 明示的にFalseを指定
        )
        assert result is not None
