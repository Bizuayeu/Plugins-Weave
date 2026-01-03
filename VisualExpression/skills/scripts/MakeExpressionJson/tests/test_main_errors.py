# tests/test_main_errors.py
"""
main.py エラーハンドリングとロギングのテスト

ファイル検証、エラーハンドリング、ロギング、パイプラインエラーのテスト。
test_main.pyから分割。
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

# main.pyのインポートパスを設定
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain import GRID_CONFIG
from main import main


class TestMainFileValidation:
    """ファイル検証のテスト"""

    @patch('sys.argv', ['main.py', '/nonexistent/file.png'])
    def test_nonexistent_file_exits_with_error(self, caplog):
        """存在しないファイルでエラー終了する"""
        import logging

        with caplog.at_level(logging.ERROR):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        assert "not found" in caplog.text.lower()


class TestMainErrorHandling:
    """エラーハンドリングのテスト"""

    @pytest.fixture
    def missing_template(self, tmp_path):
        """存在しないテンプレート"""
        test_image = Image.new(
            'RGB', (GRID_CONFIG['total_width'], GRID_CONFIG['total_height']), color='white'
        )
        input_file = tmp_path / "test_grid.png"
        test_image.save(str(input_file))

        return {
            'input_file': input_file,
            'template_file': tmp_path / "nonexistent_template.html",
            'output_dir': tmp_path / "output",
        }

    def test_missing_template_exits_with_error(self, missing_template, capsys, caplog):
        """存在しないテンプレートでエラー終了"""
        import logging

        with (
            caplog.at_level(logging.ERROR),
            patch(
                'sys.argv',
                [
                    'main.py',
                    str(missing_template['input_file']),
                    '--output',
                    str(missing_template['output_dir']),
                    '--template',
                    str(missing_template['template_file']),
                ],
            ),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        # loggingまたはprint出力をチェック
        captured = capsys.readouterr()
        assert (
            "not found" in captured.out.lower()
            or "Template" in captured.out
            or "not found" in caplog.text.lower()
            or "Template" in caplog.text
        )


class TestMainLogging:
    """ロギングのテスト"""

    @pytest.fixture
    def valid_setup(self, tmp_path):
        """有効なセットアップ"""
        test_image = Image.new(
            'RGB', (GRID_CONFIG['total_width'], GRID_CONFIG['total_height']), color='white'
        )
        input_file = tmp_path / "test_grid.png"
        test_image.save(str(input_file))

        template_file = tmp_path / "template.html"
        template_file.write_text("<html>const IMAGES={__IMAGES_PLACEHOLDER__}</html>")

        return {
            'input_file': input_file,
            'template_file': template_file,
            'output_dir': tmp_path / "output",
        }

    def test_main_uses_logging_for_info(self, valid_setup, caplog):
        """main関数がlogging.infoを使用することを確認"""
        import logging

        with (
            caplog.at_level(logging.INFO),
            patch(
                'sys.argv',
                [
                    'main.py',
                    str(valid_setup['input_file']),
                    '--output',
                    str(valid_setup['output_dir']),
                    '--template',
                    str(valid_setup['template_file']),
                    '--no-zip',
                ],
            ),
        ):
            main()

        # "Processing:" がログに含まれることを確認
        assert "Processing:" in caplog.text

    def test_main_uses_logging_for_steps(self, valid_setup, caplog):
        """各ステップがlogging.infoで出力されることを確認"""
        import logging

        with (
            caplog.at_level(logging.INFO),
            patch(
                'sys.argv',
                [
                    'main.py',
                    str(valid_setup['input_file']),
                    '--output',
                    str(valid_setup['output_dir']),
                    '--template',
                    str(valid_setup['template_file']),
                    '--no-zip',
                ],
            ),
        ):
            main()

        # 各ステップがログに含まれることを確認
        assert "Step 1/4" in caplog.text
        assert "Step 2/4" in caplog.text
        assert "Step 3/4" in caplog.text
        assert "Step 4/4" in caplog.text

    def test_error_uses_logger_error(self, caplog):
        """エラー時にlogger.errorが使用されることを確認"""
        import logging

        with (
            caplog.at_level(logging.ERROR),
            patch('sys.argv', ['main.py', '/nonexistent/file.png']),
            pytest.raises(SystemExit),
        ):
            main()

        # ERRORレベルのログが出力されていることを確認
        error_records = [r for r in caplog.records if r.levelname == "ERROR"]
        assert len(error_records) >= 1
        assert "not found" in caplog.text.lower() or "error" in caplog.text.lower()


class TestPipelineErrorHandling:
    """パイプラインエラーハンドリングのテスト"""

    @pytest.fixture
    def valid_setup(self, tmp_path):
        """有効なセットアップ"""
        test_image = Image.new(
            'RGB', (GRID_CONFIG['total_width'], GRID_CONFIG['total_height']), color='white'
        )
        input_file = tmp_path / "test_grid.png"
        test_image.save(str(input_file))

        template_file = tmp_path / "template.html"
        template_file.write_text("<html>const IMAGES={__IMAGES_PLACEHOLDER__}</html>")

        return {
            'input_file': input_file,
            'template_file': template_file,
            'output_dir': tmp_path / "output",
        }

    def test_pipeline_handles_io_error_on_json_write(self, valid_setup, caplog):
        """JSON書き込み時のIOErrorをハンドリングする"""
        import logging

        with (
            caplog.at_level(logging.ERROR),
            patch('sys.argv', [
                'main.py',
                str(valid_setup['input_file']),
                '--output', str(valid_setup['output_dir']),
                '--template', str(valid_setup['template_file']),
                '--no-zip',
            ]),
            patch('main.FileWriter.write_json', side_effect=OSError("Disk full")),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
        assert "Disk full" in caplog.text or "error" in caplog.text.lower()

    def test_pipeline_handles_io_error_on_html_write(self, valid_setup, caplog):
        """HTML書き込み時のIOErrorをハンドリングする"""
        import logging

        with (
            caplog.at_level(logging.ERROR),
            patch('sys.argv', [
                'main.py',
                str(valid_setup['input_file']),
                '--output', str(valid_setup['output_dir']),
                '--template', str(valid_setup['template_file']),
                '--no-zip',
            ]),
            patch('main.FileWriter.write_html', side_effect=OSError("Permission denied")),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
        assert "Permission denied" in caplog.text or "error" in caplog.text.lower()

    def test_pipeline_handles_unexpected_error(self, valid_setup, caplog):
        """予期しないエラーをハンドリングする"""
        import logging

        with (
            caplog.at_level(logging.ERROR),
            patch('sys.argv', [
                'main.py',
                str(valid_setup['input_file']),
                '--output', str(valid_setup['output_dir']),
                '--template', str(valid_setup['template_file']),
                '--no-zip',
            ]),
            patch('main.Base64Encoder.encode_expressions', side_effect=RuntimeError("Unexpected failure")),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()

        assert exc_info.value.code == 1
        assert "Unexpected" in caplog.text or "error" in caplog.text.lower()
