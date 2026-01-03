# tests/test_main.py
"""
main.py のテスト

CLIエントリーポイントとパイプライン実行のテスト。
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

# main.pyのインポートパスを設定
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain import GRID_CONFIG
from main import main


class TestMainArgumentParsing:
    """コマンドライン引数解析のテスト"""

    @patch('sys.argv', ['main.py', 'test_input.png'])
    @patch('main.Path')
    def test_requires_input_file(self, mock_path):
        """入力ファイルが必須であること"""
        mock_path.return_value.exists.return_value = False

        with patch('sys.exit') as mock_exit:
            mock_exit.side_effect = SystemExit(1)
            with pytest.raises(SystemExit):
                main()

    @patch('sys.argv', ['main.py'])
    def test_missing_input_shows_error(self):
        """入力ファイルがない場合エラーを表示"""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 2  # argparse error code


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


class TestMainSpecialCodes:
    """--specialオプションのテスト"""

    def test_special_codes_requires_4_items(self, caplog, tmp_path):
        """--specialは4つのコードが必要"""
        # Create a temporary valid image file
        from PIL import Image
        test_image = tmp_path / "test.png"
        img = Image.new("RGB", (1400, 1120), color="white")
        img.save(test_image)

        import logging
        with (
            patch('sys.argv', ['main.py', str(test_image), '--special', 'a,b,c']),
            caplog.at_level(logging.ERROR),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == 1
        assert "4" in caplog.text

    def test_special_codes_rejects_5_items(self, caplog, tmp_path):
        """--specialは5つ以上を拒否"""
        # Create a temporary valid image file
        from PIL import Image
        test_image = tmp_path / "test.png"
        img = Image.new("RGB", (1400, 1120), color="white")
        img.save(test_image)

        import logging
        with (
            patch('sys.argv', ['main.py', str(test_image), '--special', 'a,b,c,d,e']),
            caplog.at_level(logging.ERROR),
            pytest.raises(SystemExit) as exc_info,
        ):
            main()
        assert exc_info.value.code == 1


class TestMainPipeline:
    """パイプライン実行のテスト"""

    @pytest.fixture
    def mock_components(self, tmp_path):
        """コンポーネントのモック"""
        # テスト用の画像を作成
        test_image = Image.new('RGB', (
            GRID_CONFIG['total_width'],
            GRID_CONFIG['total_height']
        ), color='white')
        input_file = tmp_path / "test_grid.png"
        test_image.save(str(input_file))

        # テンプレートファイルを作成
        template_file = tmp_path / "template.html"
        template_file.write_text("<html>const IMAGES={__IMAGES_PLACEHOLDER__}</html>")

        return {
            'input_file': input_file,
            'template_file': template_file,
            'output_dir': tmp_path / "output",
        }

    def test_full_pipeline_creates_outputs(self, mock_components, tmp_path):
        """フルパイプラインが出力ファイルを作成する"""
        with patch('sys.argv', [
            'main.py',
            str(mock_components['input_file']),
            '--output', str(mock_components['output_dir']),
            '--template', str(mock_components['template_file']),
            '--no-zip',
        ]):
            # main()を実行
            main()

        # 出力ファイルが作成されたことを確認
        output_dir = mock_components['output_dir']
        assert (output_dir / "ExpressionImages.json").exists()
        assert (output_dir / "VisualExpressionUI.html").exists()

    def test_pipeline_with_quality_option(self, mock_components):
        """--qualityオプションが機能する"""
        with patch('sys.argv', [
            'main.py',
            str(mock_components['input_file']),
            '--output', str(mock_components['output_dir']),
            '--template', str(mock_components['template_file']),
            '--quality', '50',
            '--no-zip',
        ]):
            main()

        # 出力ファイルが作成されたことを確認
        output_dir = mock_components['output_dir']
        assert (output_dir / "ExpressionImages.json").exists()

    def test_pipeline_with_custom_special_codes(self, mock_components):
        """カスタムSpecialコードが機能する"""
        with patch('sys.argv', [
            'main.py',
            str(mock_components['input_file']),
            '--output', str(mock_components['output_dir']),
            '--template', str(mock_components['template_file']),
            '--special', 'wink,pout,smug,starry',
            '--no-zip',
        ]):
            main()

        # 出力ファイルが作成されたことを確認
        output_dir = mock_components['output_dir']
        assert (output_dir / "ExpressionImages.json").exists()


class TestMainZipCreation:
    """ZIPファイル作成のテスト"""

    @pytest.fixture
    def setup_files(self, tmp_path):
        """テスト用ファイルのセットアップ"""
        # テスト用の画像を作成
        test_image = Image.new('RGB', (
            GRID_CONFIG['total_width'],
            GRID_CONFIG['total_height']
        ), color='white')
        input_file = tmp_path / "test_grid.png"
        test_image.save(str(input_file))

        # テンプレートファイルを作成
        template_file = tmp_path / "template.html"
        template_file.write_text("<html>const IMAGES={__IMAGES_PLACEHOLDER__}</html>")

        output_dir = tmp_path / "output"

        return {
            'input_file': input_file,
            'template_file': template_file,
            'output_dir': output_dir,
        }

    def test_creates_zip_by_default(self, setup_files):
        """デフォルトでZIPファイルを作成する"""
        with patch('sys.argv', [
            'main.py',
            str(setup_files['input_file']),
            '--output', str(setup_files['output_dir']),
            '--template', str(setup_files['template_file']),
        ]):
            main()

        # ZIPファイルが作成されたことを確認
        output_dir = setup_files['output_dir']
        assert (output_dir / "VisualExpressionSkills.zip").exists()

    def test_no_zip_option_skips_zip(self, setup_files):
        """--no-zipオプションでZIP作成をスキップ"""
        with patch('sys.argv', [
            'main.py',
            str(setup_files['input_file']),
            '--output', str(setup_files['output_dir']),
            '--template', str(setup_files['template_file']),
            '--no-zip',
        ]):
            main()

        # ZIPファイルが作成されないことを確認
        output_dir = setup_files['output_dir']
        assert not (output_dir / "VisualExpressionSkills.zip").exists()


class TestMainErrorHandling:
    """エラーハンドリングのテスト"""

    @pytest.fixture
    def missing_template(self, tmp_path):
        """存在しないテンプレート"""
        test_image = Image.new('RGB', (
            GRID_CONFIG['total_width'],
            GRID_CONFIG['total_height']
        ), color='white')
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
        with caplog.at_level(logging.ERROR), patch('sys.argv', [
            'main.py',
            str(missing_template['input_file']),
            '--output', str(missing_template['output_dir']),
            '--template', str(missing_template['template_file']),
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        # loggingまたはprint出力をチェック
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "Template" in captured.out or \
               "not found" in caplog.text.lower() or "Template" in caplog.text


class TestMainLogging:
    """ロギングのテスト（Stage 1: TDD）"""

    @pytest.fixture
    def valid_setup(self, tmp_path):
        """有効なセットアップ"""
        test_image = Image.new('RGB', (
            GRID_CONFIG['total_width'],
            GRID_CONFIG['total_height']
        ), color='white')
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
        with caplog.at_level(logging.INFO), patch('sys.argv', [
            'main.py',
            str(valid_setup['input_file']),
            '--output', str(valid_setup['output_dir']),
            '--template', str(valid_setup['template_file']),
            '--no-zip',
        ]):
            main()

        # "Processing:" がログに含まれることを確認
        assert "Processing:" in caplog.text

    def test_main_uses_logging_for_steps(self, valid_setup, caplog):
        """各ステップがlogging.infoで出力されることを確認"""
        import logging
        with caplog.at_level(logging.INFO), patch('sys.argv', [
            'main.py',
            str(valid_setup['input_file']),
            '--output', str(valid_setup['output_dir']),
            '--template', str(valid_setup['template_file']),
            '--no-zip',
        ]):
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
