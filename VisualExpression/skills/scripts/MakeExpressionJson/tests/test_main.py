# tests/test_main.py
"""
main.py コアパイプラインのテスト

メインパイプライン実行のテスト。
CLI、エラーハンドリング、ZIPのテストは別ファイルに分割:
- test_main_cli.py: CLI引数解析
- test_main_errors.py: エラーハンドリングとロギング
- test_main_zip.py: ZIPファイル作成
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


class TestMainPipeline:
    """パイプライン実行のテスト"""

    @pytest.fixture
    def mock_components(self, tmp_path):
        """コンポーネントのモック"""
        # テスト用の画像を作成
        test_image = Image.new(
            'RGB', (GRID_CONFIG['total_width'], GRID_CONFIG['total_height']), color='white'
        )
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
        with patch(
            'sys.argv',
            [
                'main.py',
                str(mock_components['input_file']),
                '--output',
                str(mock_components['output_dir']),
                '--template',
                str(mock_components['template_file']),
                '--no-zip',
            ],
        ):
            # main()を実行
            main()

        # 出力ファイルが作成されたことを確認
        output_dir = mock_components['output_dir']
        assert (output_dir / "ExpressionImages.json").exists()
        assert (output_dir / "VisualExpressionUI.html").exists()

    def test_pipeline_with_quality_option(self, mock_components):
        """--qualityオプションが機能する"""
        with patch(
            'sys.argv',
            [
                'main.py',
                str(mock_components['input_file']),
                '--output',
                str(mock_components['output_dir']),
                '--template',
                str(mock_components['template_file']),
                '--quality',
                '50',
                '--no-zip',
            ],
        ):
            main()

        # 出力ファイルが作成されたことを確認
        output_dir = mock_components['output_dir']
        assert (output_dir / "ExpressionImages.json").exists()

    def test_pipeline_with_custom_special_codes(self, mock_components):
        """カスタムSpecialコードが機能する"""
        with patch(
            'sys.argv',
            [
                'main.py',
                str(mock_components['input_file']),
                '--output',
                str(mock_components['output_dir']),
                '--template',
                str(mock_components['template_file']),
                '--special',
                'wink,pout,smug,starry',
                '--no-zip',
            ],
        ):
            main()

        # 出力ファイルが作成されたことを確認
        output_dir = mock_components['output_dir']
        assert (output_dir / "ExpressionImages.json").exists()
