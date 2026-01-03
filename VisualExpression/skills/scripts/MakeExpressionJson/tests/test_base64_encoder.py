"""Tests for usecases.base64_encoder module."""

import base64

import pytest
from PIL import Image

from usecases.base64_encoder import Base64Encoder


class TestBase64EncoderValidation:
    """Tests for Base64Encoder input validation."""

    def test_rejects_quality_below_1(self):
        """品質が1未満の場合はValueErrorを発生"""
        with pytest.raises(ValueError, match="Quality must be 1-100"):
            Base64Encoder(quality=0)

    def test_rejects_quality_above_100(self):
        """品質が100超の場合はValueErrorを発生"""
        with pytest.raises(ValueError, match="Quality must be 1-100"):
            Base64Encoder(quality=101)

    def test_rejects_negative_quality(self):
        """負の品質値はValueErrorを発生"""
        with pytest.raises(ValueError, match="Quality must be 1-100"):
            Base64Encoder(quality=-1)

    def test_accepts_valid_quality(self):
        """有効な品質値（85）は受け入れる"""
        encoder = Base64Encoder(quality=85)
        assert encoder.quality == 85

    @pytest.mark.parametrize("quality", [1, 50, 85, 100])
    def test_boundary_qualities(self, quality):
        """境界値テスト: 1, 50, 85, 100"""
        encoder = Base64Encoder(quality=quality)
        assert encoder.quality == quality


class TestBase64EncoderFunctionality:
    """Tests for Base64Encoder core functionality."""

    def test_encode_image_returns_string(self, create_test_grid_image):
        """画像エンコードは文字列を返す"""
        encoder = Base64Encoder()
        img = create_test_grid_image(100, 100)
        result = encoder.encode_image(img)
        assert isinstance(result, str)

    def test_encode_image_returns_valid_base64(self, create_test_grid_image):
        """エンコード結果は有効なBase64文字列"""
        encoder = Base64Encoder()
        img = create_test_grid_image(100, 100)
        result = encoder.encode_image(img)
        # Base64デコード可能か確認
        decoded = base64.b64decode(result)
        assert len(decoded) > 0

    def test_encode_expressions_returns_expression_set(self, sample_expression_images):
        """encode_expressionsはExpressionSetを返す"""
        encoder = Base64Encoder()
        result = encoder.encode_expressions(sample_expression_images)
        assert len(result) == 20
        assert "normal" in result.expressions

    def test_encode_expressions_all_have_base64_data(self, sample_expression_images):
        """全表情にbase64_dataが設定される"""
        encoder = Base64Encoder()
        result = encoder.encode_expressions(sample_expression_images)
        for _code, expr in result.expressions.items():
            assert expr.base64_data is not None
            assert len(expr.base64_data) > 0

    def test_to_json_dict_format(self, sample_expression_images):
        """to_json_dictは正しい形式のdictを返す"""
        encoder = Base64Encoder()
        expression_set = encoder.encode_expressions(sample_expression_images)
        result = encoder.to_json_dict(expression_set)

        assert isinstance(result, dict)
        assert "normal" in result
        # data URI形式であることを確認
        assert result["normal"].startswith("data:image/jpeg;base64,")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
