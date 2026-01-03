"""Protocol抽象化のTDDテスト (Task 2: Protocol abstraction)"""

import pytest


class TestProtocolModuleExists:
    """usecases/protocols.pyが存在することを確認"""

    def test_protocols_module_importable(self):
        """protocols モジュールがインポート可能"""
        from usecases import protocols

        # モジュールが正しくインポートされたことを確認
        assert protocols is not None


class TestImageSplitterProtocol:
    """ImageSplitterProtocolのテスト"""

    def test_protocol_exists(self):
        """ImageSplitterProtocolが定義されている"""
        from usecases.protocols import ImageSplitterProtocol

        # runtime_checkable なので __protocol_attrs__ を持つ
        assert hasattr(ImageSplitterProtocol, "__protocol_attrs__")

    def test_image_splitter_implements_protocol(self):
        """ImageSplitterがプロトコルを実装している"""
        from usecases.image_splitter import ImageSplitter
        from usecases.protocols import ImageSplitterProtocol

        splitter = ImageSplitter()
        assert isinstance(splitter, ImageSplitterProtocol)

    def test_protocol_has_validate_image_method(self):
        """プロトコルにvalidate_imageメソッドが定義されている"""
        from usecases.protocols import ImageSplitterProtocol

        assert "validate_image" in ImageSplitterProtocol.__protocol_attrs__

    def test_protocol_has_split_method(self):
        """プロトコルにsplitメソッドが定義されている"""
        from usecases.protocols import ImageSplitterProtocol

        assert "split" in ImageSplitterProtocol.__protocol_attrs__

    def test_protocol_has_split_from_file_method(self):
        """プロトコルにsplit_from_fileメソッドが定義されている"""
        from usecases.protocols import ImageSplitterProtocol

        assert "split_from_file" in ImageSplitterProtocol.__protocol_attrs__


class TestBase64EncoderProtocol:
    """Base64EncoderProtocolのテスト"""

    def test_protocol_exists(self):
        """Base64EncoderProtocolが定義されている"""
        from usecases.protocols import Base64EncoderProtocol

        assert hasattr(Base64EncoderProtocol, "__protocol_attrs__")

    def test_base64_encoder_implements_protocol(self):
        """Base64Encoderがプロトコルを実装している"""
        from usecases.base64_encoder import Base64Encoder
        from usecases.protocols import Base64EncoderProtocol

        encoder = Base64Encoder()
        assert isinstance(encoder, Base64EncoderProtocol)

    def test_protocol_has_encode_image_method(self):
        """プロトコルにencode_imageメソッドが定義されている"""
        from usecases.protocols import Base64EncoderProtocol

        assert "encode_image" in Base64EncoderProtocol.__protocol_attrs__

    def test_protocol_has_encode_expressions_method(self):
        """プロトコルにencode_expressionsメソッドが定義されている"""
        from usecases.protocols import Base64EncoderProtocol

        assert "encode_expressions" in Base64EncoderProtocol.__protocol_attrs__

    def test_protocol_has_to_json_dict_method(self):
        """プロトコルにto_json_dictメソッドが定義されている"""
        from usecases.protocols import Base64EncoderProtocol

        assert "to_json_dict" in Base64EncoderProtocol.__protocol_attrs__


class TestProtocolUsability:
    """プロトコルの実用性テスト"""

    def test_mock_splitter_satisfies_protocol(self):
        """モックオブジェクトがプロトコルを満たすことを確認"""
        from unittest.mock import MagicMock

        from usecases.protocols import ImageSplitterProtocol

        mock = MagicMock()
        mock.validate_image = MagicMock(return_value=(True, ""))
        mock.split = MagicMock(return_value=[])
        mock.split_from_file = MagicMock(return_value=[])

        # MagicMockはすべてのメソッドを持つのでプロトコルを満たす
        assert isinstance(mock, ImageSplitterProtocol)

    def test_mock_encoder_satisfies_protocol(self):
        """モックオブジェクトがプロトコルを満たすことを確認"""
        from unittest.mock import MagicMock

        from usecases.protocols import Base64EncoderProtocol

        mock = MagicMock()
        mock.encode_image = MagicMock(return_value="base64string")
        mock.encode_expressions = MagicMock()
        mock.to_json_dict = MagicMock(return_value={})

        assert isinstance(mock, Base64EncoderProtocol)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
