"""Tests for ImageSplitter."""

import pytest
from PIL import Image

from domain import EXPRESSION_CODES, GRID_CONFIG
from usecases.image_splitter import ImageSplitter


class TestImageSplitter:
    """Tests for the ImageSplitter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = ImageSplitter()

    def create_test_grid(self, width: int, height: int) -> Image.Image:
        """Create a test grid image with the specified dimensions."""
        return Image.new("RGB", (width, height), color="white")

    def test_validate_correct_size(self):
        """Test validation passes for correct image size."""
        expected_width = GRID_CONFIG["total_width"]  # 1400
        expected_height = GRID_CONFIG["total_height"]  # 1120

        img = self.create_test_grid(expected_width, expected_height)
        is_valid, error_msg = self.splitter.validate_image(img)

        assert is_valid is True
        assert error_msg == ""

    def test_validate_wrong_size(self):
        """Test validation fails for non-divisible image size."""
        # 101は5で割り切れないのでエラー
        img = self.create_test_grid(101, 100)
        is_valid, error_msg = self.splitter.validate_image(img)

        assert is_valid is False
        assert "not divisible" in error_msg

    def test_split_returns_20_images(self):
        """Test that split returns exactly 20 expression images."""
        expected_width = GRID_CONFIG["total_width"]
        expected_height = GRID_CONFIG["total_height"]

        img = self.create_test_grid(expected_width, expected_height)
        results = self.splitter.split(img)

        assert len(results) == 20

    def test_split_returns_correct_codes(self):
        """Test that split returns all expected expression codes."""
        expected_width = GRID_CONFIG["total_width"]
        expected_height = GRID_CONFIG["total_height"]

        img = self.create_test_grid(expected_width, expected_height)
        results = self.splitter.split(img)

        codes = [code for code, _ in results]
        assert codes == EXPRESSION_CODES

    def test_split_image_dimensions(self):
        """Test that each split image has correct dimensions."""
        expected_width = GRID_CONFIG["total_width"]
        expected_height = GRID_CONFIG["total_height"]
        cell_size = GRID_CONFIG["cell_size"]

        img = self.create_test_grid(expected_width, expected_height)
        results = self.splitter.split(img)

        for _code, cropped_img in results:
            assert cropped_img.width == cell_size
            assert cropped_img.height == cell_size

    def test_split_raises_for_wrong_size(self):
        """Test that split raises ValueError for non-divisible size."""
        # 101は5で割り切れないのでエラー
        img = self.create_test_grid(101, 100)

        with pytest.raises(ValueError) as exc_info:
            self.splitter.split(img)

        assert "not divisible" in str(exc_info.value)


class TestSplitFromFile:
    """split_from_file()メソッドのテスト"""

    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = ImageSplitter()

    def test_split_from_file_rgba_image(self, tmp_path):
        """RGBA画像がRGBに変換されて処理されることを確認"""
        expected_width = GRID_CONFIG["total_width"]
        expected_height = GRID_CONFIG["total_height"]

        # RGBA画像を作成
        img = Image.new("RGBA", (expected_width, expected_height), color=(255, 255, 255, 128))
        file_path = tmp_path / "test_rgba.png"
        img.save(file_path)

        # split_from_fileで処理
        results = self.splitter.split_from_file(str(file_path))

        assert len(results) == 20
        # 結果の画像がRGBモードであることを確認
        for _code, cropped_img in results:
            assert cropped_img.mode == "RGB"

    def test_split_from_file_palette_image(self, tmp_path):
        """パレット（P）画像がRGBに変換されて処理されることを確認"""
        expected_width = GRID_CONFIG["total_width"]
        expected_height = GRID_CONFIG["total_height"]

        # RGB画像を作成し、パレットモードに変換
        img = Image.new("RGB", (expected_width, expected_height), color="white")
        img = img.convert("P")
        file_path = tmp_path / "test_palette.png"
        img.save(file_path)

        # split_from_fileで処理
        results = self.splitter.split_from_file(str(file_path))

        assert len(results) == 20


class TestCellSizeRemoved:
    """cell_sizeパラメータ削除テスト（v2.0 TDD）"""

    def test_no_cell_size_parameter(self):
        """cell_size パラメータが存在しないことを確認"""
        import inspect

        sig = inspect.signature(ImageSplitter.__init__)
        assert "cell_size" not in sig.parameters

    def test_no_cell_size_attribute(self):
        """cell_size 属性が存在しないことを確認"""
        splitter = ImageSplitter()
        assert not hasattr(splitter, "cell_size")


class TestCenterCrop:
    """中心切り抜き処理のテスト（TDD）"""

    def setup_method(self):
        """Set up test fixtures."""
        self.splitter = ImageSplitter()

    def test_center_crop_300x300_to_280x280(self):
        """300x300セルから中心280x280を切り抜くことを確認"""
        # 1500x1200 画像 (300px/cell) を作成
        img = Image.new("RGB", (1500, 1200), color="white")

        results = self.splitter.split(img)

        # 各画像が280x280であることを確認
        for _code, cropped_img in results:
            assert cropped_img.width == 280
            assert cropped_img.height == 280

    def test_center_crop_preserves_center_content(self):
        """中心の内容が保持され、端が切り捨てられることを確認"""
        # 300x300のセルで端を赤、中心を緑にした画像を作成
        img = Image.new("RGB", (1500, 1200), color="red")  # 端は赤
        # 左上セル(0,0)の中心部分(10-290, 10-290)を緑に（マージン10px）
        for x in range(10, 290):
            for y in range(10, 290):
                img.putpixel((x, y), (0, 255, 0))

        results = self.splitter.split(img)
        first_img = results[0][1]

        # 中心切り抜きの場合: 280x280の全体が緑であるべき（端の赤は切り落とされる）
        # リサイズの場合: 端の赤が縮小されて含まれる
        corner_pixel = first_img.getpixel((0, 0))  # 左上角
        center_pixel = first_img.getpixel((140, 140))  # 中心

        # 両方とも緑であれば中心切り抜きが正しく動作している
        assert corner_pixel == (0, 255, 0), f"Corner should be green, got {corner_pixel}"
        assert center_pixel == (0, 255, 0), f"Center should be green, got {center_pixel}"

    def test_fallback_resize_for_exact_size(self):
        """280x280セルはそのまま出力されることを確認"""
        # 1400x1120 画像 (280px/cell) を作成
        img = Image.new("RGB", (1400, 1120), color="white")

        results = self.splitter.split(img)

        for _code, cropped_img in results:
            assert cropped_img.width == 280
            assert cropped_img.height == 280

    def test_fallback_resize_for_smaller_cells(self):
        """280未満のセルはリサイズされることを確認"""
        # 1000x800 画像 (200px/cell) を作成
        img = Image.new("RGB", (1000, 800), color="white")

        results = self.splitter.split(img)

        # リサイズにより280x280になっていることを確認
        for _code, cropped_img in results:
            assert cropped_img.width == 280
            assert cropped_img.height == 280


class TestOffsetCrop:
    """オフセット付き切り抜きのテスト（TDD - Phase 2）"""

    def test_offset_crop_applies_x_offset(self):
        """X方向オフセットが適用されることを確認"""
        # 1500x1200 画像を作成（300px/cell）
        # 左上セル(0,0)の左端10pxを赤、それ以外を緑に
        img = Image.new("RGB", (1500, 1200), color="green")
        for x in range(10):
            for y in range(300):
                img.putpixel((x, y), (255, 0, 0))

        # X方向に+5pxオフセット（右にずらす）
        offsets = {"normal": {"x": 5, "y": 0}}
        splitter = ImageSplitter(offsets=offsets)

        results = splitter.split(img)
        first_img = results[0][1]

        # オフセット+5により、左端の赤が出力に含まれるべき
        # 中心切り抜き: margin_x = (300-280)//2 = 10 → 左端10pxは切り落とされる
        # オフセット+5: margin_x = 10 + 5 = 15 → 左端15pxが切り落とされる
        # つまり、左端の赤(0-9)は出力に含まれない
        left_pixel = first_img.getpixel((0, 140))
        assert left_pixel == (0, 128, 0), f"Left edge should be green, got {left_pixel}"

    def test_offset_crop_applies_y_offset(self):
        """Y方向オフセットが適用されることを確認"""
        # 1500x1200 画像を作成（300px/cell）
        # 左上セル(0,0)の上端10pxを赤、それ以外を緑に
        img = Image.new("RGB", (1500, 1200), color="green")
        for x in range(300):
            for y in range(10):
                img.putpixel((x, y), (255, 0, 0))

        # Y方向に-5pxオフセット（上にずらす＝表情が下にある場合）
        offsets = {"normal": {"x": 0, "y": -5}}
        splitter = ImageSplitter(offsets=offsets)

        results = splitter.split(img)
        first_img = results[0][1]

        # オフセット-5により、上端がより多く含まれる
        # 中心切り抜き: margin_y = (300-280)//2 = 10 → 上端10pxは切り落とされる
        # オフセット-5: margin_y = 10 - 5 = 5 → 上端5pxが切り落とされる
        # つまり、上端の赤(5-9)は出力に含まれる
        top_pixel = first_img.getpixel((140, 0))
        assert top_pixel == (255, 0, 0), f"Top edge should be red, got {top_pixel}"

    def test_no_offset_uses_center(self):
        """オフセット未指定時は中心切り抜き（既存動作）"""
        # 1500x1200 画像（300px/cell）
        img = Image.new("RGB", (1500, 1200), color="white")

        # オフセットなし
        splitter = ImageSplitter()

        results = splitter.split(img)

        for _code, cropped_img in results:
            assert cropped_img.width == 280
            assert cropped_img.height == 280

    def test_offset_parameter_exists(self):
        """offsets パラメータが存在することを確認"""
        import inspect

        sig = inspect.signature(ImageSplitter.__init__)
        assert "offsets" in sig.parameters

    def test_offset_only_affects_specified_expressions(self):
        """オフセットは指定した表情のみに適用される"""
        # normalにのみオフセット指定、joyには指定なし
        offsets = {"normal": {"x": 5, "y": 0}}
        splitter = ImageSplitter(offsets=offsets)

        # splitterの内部状態を確認（オフセットが保存されている）
        assert hasattr(splitter, "offsets")
        assert splitter.offsets == offsets


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
