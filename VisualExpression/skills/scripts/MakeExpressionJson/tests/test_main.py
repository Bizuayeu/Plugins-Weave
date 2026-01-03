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

from domain.constants import GRID_CONFIG
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
    def test_nonexistent_file_exits_with_error(self, capsys):
        """存在しないファイルでエラー終了する"""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "Error" in captured.out


class TestMainSpecialCodes:
    """--specialオプションのテスト"""

    @patch('sys.argv', ['main.py', 'test.png', '--special', 'a,b,c'])
    def test_special_codes_requires_4_items(self, capsys):
        """--specialは4つのコードが必要"""
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "4" in captured.out

    @patch('sys.argv', ['main.py', 'test.png', '--special', 'a,b,c,d,e'])
    def test_special_codes_rejects_5_items(self, capsys):
        """--specialは5つ以上を拒否"""
        with pytest.raises(SystemExit) as exc_info:
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

    def test_missing_template_exits_with_error(self, missing_template, capsys):
        """存在しないテンプレートでエラー終了"""
        with patch('sys.argv', [
            'main.py',
            str(missing_template['input_file']),
            '--output', str(missing_template['output_dir']),
            '--template', str(missing_template['template_file']),
        ]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "Template" in captured.out
