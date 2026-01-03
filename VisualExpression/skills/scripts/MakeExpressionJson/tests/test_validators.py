"""
test_validators.py - バリデーション関数のテスト (TDD RED Phase)

domain/validators.pyの共有バリデーションロジックをテスト
"""

import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestValidateGridDimensions:
    """グリッド次元バリデーションのテスト"""

    def test_valid_dimensions_return_true(self):
        """正しい次元は (True, '') を返す"""
        from domain.validators import validate_grid_dimensions

        is_valid, msg = validate_grid_dimensions(
            width=1400, height=1120, cols=5, rows=4
        )
        assert is_valid is True
        assert msg == ""

    def test_width_not_divisible_returns_false(self):
        """幅が列数で割り切れない場合 (False, message) を返す"""
        from domain.validators import validate_grid_dimensions

        is_valid, msg = validate_grid_dimensions(
            width=1401, height=1120, cols=5, rows=4
        )
        assert is_valid is False
        assert "width" in msg.lower()
        assert "1401" in msg
        assert "5" in msg

    def test_height_not_divisible_returns_false(self):
        """高さが行数で割り切れない場合 (False, message) を返す"""
        from domain.validators import validate_grid_dimensions

        is_valid, msg = validate_grid_dimensions(
            width=1400, height=1121, cols=5, rows=4
        )
        assert is_valid is False
        assert "height" in msg.lower()
        assert "1121" in msg
        assert "4" in msg

    def test_error_message_includes_recommended_size(self):
        """エラーメッセージに推奨サイズが含まれる"""
        from domain.validators import validate_grid_dimensions

        is_valid, msg = validate_grid_dimensions(
            width=1401, height=1120, cols=5, rows=4, cell_size=280
        )
        assert is_valid is False
        assert "1400" in msg  # 推奨幅: 5 * 280 = 1400

    def test_height_error_includes_recommended_size(self):
        """高さエラーメッセージに推奨サイズが含まれる"""
        from domain.validators import validate_grid_dimensions

        is_valid, msg = validate_grid_dimensions(
            width=1400, height=1121, cols=5, rows=4, cell_size=280
        )
        assert is_valid is False
        assert "1120" in msg  # 推奨高さ: 4 * 280 = 1120

    def test_smaller_valid_dimensions(self):
        """小さいが有効な次元もパス"""
        from domain.validators import validate_grid_dimensions

        is_valid, msg = validate_grid_dimensions(
            width=700, height=560, cols=5, rows=4
        )
        assert is_valid is True
        assert msg == ""

    def test_without_cell_size_still_validates(self):
        """cell_sizeなしでもバリデーション可能"""
        from domain.validators import validate_grid_dimensions

        is_valid, msg = validate_grid_dimensions(
            width=1401, height=1120, cols=5, rows=4
        )
        assert is_valid is False
        assert "width" in msg.lower()

    def test_both_invalid_returns_width_error_first(self):
        """幅・高さ両方無効な場合、幅エラーを先に返す"""
        from domain.validators import validate_grid_dimensions

        is_valid, msg = validate_grid_dimensions(
            width=1401, height=1121, cols=5, rows=4
        )
        assert is_valid is False
        assert "width" in msg.lower()


class TestValidateImageDimensions:
    """PIL Imageバリデーションのテスト"""

    def test_validate_image_dimensions_valid(self):
        """有効なPIL Imageは (True, '') を返す"""
        from domain.validators import validate_image_dimensions

        img = Image.new("RGB", (1400, 1120))
        is_valid, msg = validate_image_dimensions(image=img, cols=5, rows=4)
        assert is_valid is True
        assert msg == ""

    def test_validate_image_dimensions_invalid_width(self):
        """無効な幅のPIL Imageはエラーを返す"""
        from domain.validators import validate_image_dimensions

        img = Image.new("RGB", (101, 100))
        is_valid, msg = validate_image_dimensions(image=img, cols=5, rows=4)
        assert is_valid is False
        assert "101" in msg

    def test_validate_image_dimensions_with_cell_size(self):
        """cell_size付きでPIL Imageをバリデート"""
        from domain.validators import validate_image_dimensions

        img = Image.new("RGB", (1401, 1120))
        is_valid, msg = validate_image_dimensions(
            image=img, cols=5, rows=4, cell_size=280
        )
        assert is_valid is False
        assert "1400" in msg  # 推奨サイズ

    def test_validate_image_rgba_mode(self):
        """RGBA画像も正しくバリデート"""
        from domain.validators import validate_image_dimensions

        img = Image.new("RGBA", (1400, 1120))
        is_valid, msg = validate_image_dimensions(image=img, cols=5, rows=4)
        assert is_valid is True


class TestValidatorsIntegration:
    """validators統合テスト"""

    def test_default_grid_config_values(self):
        """GRID_CONFIGのデフォルト値で正しく動作"""
        from domain.validators import validate_grid_dimensions

        # デフォルト設定: 5列 × 4行 × 280px = 1400×1120
        is_valid, msg = validate_grid_dimensions(
            width=1400, height=1120, cols=5, rows=4, cell_size=280
        )
        assert is_valid is True

    def test_validate_grid_dimensions_type_hints(self):
        """型ヒントが正しく定義されている"""
        from domain.validators import validate_grid_dimensions

        # 関数が存在し、呼び出し可能
        result = validate_grid_dimensions(
            width=1400, height=1120, cols=5, rows=4
        )
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], bool)
        assert isinstance(result[1], str)
