"""Integration tests for the full expression processing pipeline."""

import pytest
from PIL import Image

from domain import CELL_SIZE, EXPRESSION_CODES, GRID_COLS, GRID_ROWS
from usecases.base64_encoder import Base64Encoder
from usecases.html_builder import HtmlBuilder
from usecases.image_splitter import ImageSplitter


class TestFullPipeline:
    """End-to-end integration tests."""

    def test_full_pipeline_from_image_to_html(self, create_test_grid_image, tmp_path):
        """画像→分割→エンコード→HTML生成の全パイプライン"""
        # Arrange: グリッド画像とテンプレートを準備
        grid_img = create_test_grid_image(GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE)
        template = tmp_path / "template.html"
        template.write_text(
            "<html><script>const IMAGES={__IMAGES_PLACEHOLDER__}</script></html>", encoding="utf-8"
        )

        # Act: パイプライン実行
        splitter = ImageSplitter()
        expressions = splitter.split(grid_img)

        encoder = Base64Encoder()
        encoded = encoder.encode_expressions(expressions)

        builder = HtmlBuilder(str(template))
        images_dict = encoder.to_json_dict(encoded)
        html = builder.build(images_dict)

        # Assert
        assert len(expressions) == 20
        # JSON形式（ダブルクォート）
        assert '"normal":' in html
        assert '"smile":' in html
        assert '"dreamy":' in html
        assert "__IMAGES_PLACEHOLDER__" not in html

    def test_pipeline_preserves_all_expression_codes(self, create_test_grid_image, tmp_path):
        """パイプラインは全20表情コードを保持"""
        grid_img = create_test_grid_image()
        template = tmp_path / "template.html"
        template.write_text(
            "<script>const IMAGES={__IMAGES_PLACEHOLDER__}</script>", encoding="utf-8"
        )

        splitter = ImageSplitter()
        expressions = splitter.split(grid_img)
        encoder = Base64Encoder()
        encoded = encoder.encode_expressions(expressions)
        builder = HtmlBuilder(str(template))
        html = builder.build(encoder.to_json_dict(encoded))

        # 全表情コードがHTMLに含まれることを確認（JSON形式）
        for code in EXPRESSION_CODES:
            assert f'"{code}":' in html, f"Missing expression code: {code}"


class TestSpecialCodesCustomization:
    """Tests for custom Special codes feature."""

    def test_custom_special_codes(self, create_test_grid_image):
        """カスタムSpecialコードでのパイプライン"""
        grid_img = create_test_grid_image()
        custom_codes = ["custom1", "custom2", "custom3", "custom4"]

        splitter = ImageSplitter(special_codes=custom_codes)
        expressions = splitter.split(grid_img)

        codes = [code for code, _ in expressions]

        # カスタムコードが含まれている
        for code in custom_codes:
            assert code in codes, f"Missing custom code: {code}"

        # デフォルトのSpecialコードは含まれていない
        assert "sleepy" not in codes
        assert "cynical" not in codes
        assert "defeated" not in codes
        assert "dreamy" not in codes

    def test_custom_special_codes_count(self, create_test_grid_image):
        """カスタムSpecialコードでも合計20個"""
        grid_img = create_test_grid_image()
        custom_codes = ["a", "b", "c", "d"]

        splitter = ImageSplitter(special_codes=custom_codes)
        expressions = splitter.split(grid_img)

        assert len(expressions) == 20


class TestEdgeCases:
    """Edge case and error handling tests."""

    def test_different_image_sizes(self, create_test_grid_image):
        """異なる画像サイズへの対応（grid分割可能なサイズ）"""
        # 標準の半分のサイズ
        small_img = create_test_grid_image(700, 560)

        splitter = ImageSplitter()
        expressions = splitter.split(small_img)

        assert len(expressions) == 20
        # リサイズされて出力サイズになっている
        for _, img in expressions:
            assert img.width == CELL_SIZE
            assert img.height == CELL_SIZE

    def test_invalid_image_size_raises(self, create_test_grid_image):
        """grid分割不可能なサイズはエラー"""
        # 5で割り切れない幅
        bad_img = create_test_grid_image(701, 560)

        splitter = ImageSplitter()

        with pytest.raises(ValueError, match="not divisible"):
            splitter.split(bad_img)

    def test_encoder_quality_affects_output_size(self):
        """エンコーダー品質が出力サイズに影響"""
        # ノイズのある画像を生成（圧縮効果が出やすい）
        import random

        img = Image.new("RGB", (CELL_SIZE, CELL_SIZE))
        pixels = img.load()
        for x in range(CELL_SIZE):
            for y in range(CELL_SIZE):
                pixels[x, y] = (
                    random.randint(0, 255),
                    random.randint(0, 255),
                    random.randint(0, 255),
                )

        low_quality = Base64Encoder(quality=10)
        high_quality = Base64Encoder(quality=100)

        low_result = low_quality.encode_image(img)
        high_result = high_quality.encode_image(img)

        # 低品質の方がサイズが小さい
        assert len(low_result) < len(high_result)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
