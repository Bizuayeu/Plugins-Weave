"""Error handling test cases for MakeExpressionJson (Stage 6: TDD)."""

import pytest
from PIL import Image

from domain import build_expression_codes, SPECIAL_CODES_COUNT
from usecases.image_splitter import ImageSplitter
from usecases.html_builder import HtmlBuilder


class TestSpecialCodesValidation:
    """Special codesバリデーションのエラーケーステスト"""

    def test_invalid_special_codes_count_3(self):
        """--special に3個を渡した場合のエラー処理"""
        with pytest.raises(ValueError) as exc:
            build_expression_codes(["a", "b", "c"])  # 3個

        assert "3" in str(exc.value)
        assert str(SPECIAL_CODES_COUNT) in str(exc.value)

    def test_invalid_special_codes_count_5(self):
        """--special に5個を渡した場合のエラー処理"""
        with pytest.raises(ValueError) as exc:
            build_expression_codes(["a", "b", "c", "d", "e"])  # 5個

        assert "5" in str(exc.value)

    def test_invalid_special_codes_count_0(self):
        """空リストを渡した場合のエラー処理"""
        with pytest.raises(ValueError) as exc:
            build_expression_codes([])

        assert "0" in str(exc.value)

    def test_splitter_with_invalid_special_codes(self):
        """ImageSplitterに不正なspecial_codesを渡した場合"""
        with pytest.raises(ValueError) as exc:
            ImageSplitter(special_codes=["only", "two"])

        assert "2" in str(exc.value)


class TestHtmlBuilderErrors:
    """HtmlBuilder関連のエラーケーステスト"""

    def test_template_not_found(self, tmp_path):
        """テンプレートファイルが存在しない場合"""
        nonexistent = tmp_path / "nonexistent.html"

        with pytest.raises(FileNotFoundError):
            HtmlBuilder(str(nonexistent))

    def test_template_missing_placeholder(self, tmp_path):
        """テンプレートにプレースホルダーがない場合"""
        template = tmp_path / "bad_template.html"
        template.write_text("<html><body>No placeholder</body></html>")

        builder = HtmlBuilder(str(template))

        with pytest.raises(ValueError) as exc:
            builder.load_template()

        assert "__IMAGES_PLACEHOLDER__" in str(exc.value)


class TestImageSplitterErrors:
    """ImageSplitter関連のエラーケーステスト"""

    def test_image_dimensions_not_divisible_by_cols(self):
        """グリッドで割り切れない画像幅"""
        # 101は5で割り切れない
        img = Image.new("RGB", (101, 100), color="white")
        splitter = ImageSplitter()

        with pytest.raises(ValueError) as exc:
            splitter.split(img)

        assert "not divisible" in str(exc.value)
        assert "101" in str(exc.value)

    def test_image_dimensions_not_divisible_by_rows(self):
        """グリッドで割り切れない画像高さ"""
        # 100は4で割り切れない（100 / 4 = 25...）実際には割り切れる
        # 101は4で割り切れない
        img = Image.new("RGB", (100, 101), color="white")
        splitter = ImageSplitter()

        with pytest.raises(ValueError) as exc:
            splitter.split(img)

        assert "not divisible" in str(exc.value)

    def test_image_too_small(self):
        """極端に小さい画像"""
        img = Image.new("RGB", (1, 1), color="white")
        splitter = ImageSplitter()

        with pytest.raises(ValueError) as exc:
            splitter.split(img)

        assert "not divisible" in str(exc.value)


class TestQualityBoundaries:
    """品質パラメータの境界テスト"""

    def test_quality_1_is_valid(self):
        """quality=1は有効"""
        from usecases.base64_encoder import Base64Encoder

        encoder = Base64Encoder(quality=1)
        assert encoder.quality == 1

    def test_quality_100_is_valid(self):
        """quality=100は有効"""
        from usecases.base64_encoder import Base64Encoder

        encoder = Base64Encoder(quality=100)
        assert encoder.quality == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
