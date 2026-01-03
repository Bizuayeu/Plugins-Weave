# tests/test_main_cli.py
"""
main.py CLI引数解析のテスト

コマンドライン引数解析と--specialオプションのテスト。
test_main.pyから分割。
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

# main.pyのインポートパスを設定
sys.path.insert(0, str(Path(__file__).parent.parent))

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
