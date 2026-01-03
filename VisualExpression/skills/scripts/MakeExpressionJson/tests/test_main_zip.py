# tests/test_main_zip.py
"""
main.py ZIPファイル作成のテスト

ZIPファイル作成と--no-zipオプションのテスト。
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


class TestMainZipCreation:
    """ZIPファイル作成のテスト"""

    @pytest.fixture
    def setup_files(self, tmp_path):
        """テスト用ファイルのセットアップ"""
        # テスト用の画像を作成
        test_image = Image.new(
            'RGB', (GRID_CONFIG['total_width'], GRID_CONFIG['total_height']), color='white'
        )
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
        with patch(
            'sys.argv',
            [
                'main.py',
                str(setup_files['input_file']),
                '--output',
                str(setup_files['output_dir']),
                '--template',
                str(setup_files['template_file']),
            ],
        ):
            main()

        # ZIPファイルが作成されたことを確認
        output_dir = setup_files['output_dir']
        assert (output_dir / "VisualExpressionSkills.zip").exists()

    def test_no_zip_option_skips_zip(self, setup_files):
        """--no-zipオプションでZIP作成をスキップ"""
        with patch(
            'sys.argv',
            [
                'main.py',
                str(setup_files['input_file']),
                '--output',
                str(setup_files['output_dir']),
                '--template',
                str(setup_files['template_file']),
                '--no-zip',
            ],
        ):
            main()

        # ZIPファイルが作成されないことを確認
        output_dir = setup_files['output_dir']
        assert not (output_dir / "VisualExpressionSkills.zip").exists()
