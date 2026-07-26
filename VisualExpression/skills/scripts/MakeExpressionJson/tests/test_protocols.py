"""Protocol抽象化のTDDテスト (Task 2: Protocol abstraction)"""

from types import SimpleNamespace

import pytest

# プロトコルが要求するメソッド群。
# typing の内部属性（__protocol_attrs__ は CPython 3.12+ のみ）ではなく、
# runtime_checkable な isinstance という公開挙動で検証する。
SPLITTER_METHODS = ("validate_image", "split", "split_from_file")
ENCODER_METHODS = ("encode_image", "encode_expressions", "to_json_dict")


def _stub(methods):
    """指定メソッドのみを持つスタブオブジェクトを返す"""
    return SimpleNamespace(**{name: (lambda *args, **kwargs: None) for name in methods})


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
        """ImageSplitterProtocolが定義され、runtime_checkableである"""
        from usecases.protocols import ImageSplitterProtocol

        # runtime_checkable でなければ isinstance が TypeError を投げる
        assert not isinstance(object(), ImageSplitterProtocol)

    def test_image_splitter_implements_protocol(self):
        """ImageSplitterがプロトコルを実装している"""
        from usecases.image_splitter import ImageSplitter
        from usecases.protocols import ImageSplitterProtocol

        splitter = ImageSplitter()
        assert isinstance(splitter, ImageSplitterProtocol)

    def test_protocol_accepts_full_stub(self):
        """3メソッドを揃えたオブジェクトはプロトコルを満たす"""
        from usecases.protocols import ImageSplitterProtocol

        assert isinstance(_stub(SPLITTER_METHODS), ImageSplitterProtocol)

    @pytest.mark.parametrize("missing", SPLITTER_METHODS)
    def test_protocol_requires_each_method(self, missing):
        """各メソッドはプロトコルの必須要素（欠けると適合しない）"""
        from usecases.protocols import ImageSplitterProtocol

        incomplete = _stub([m for m in SPLITTER_METHODS if m != missing])
        assert not isinstance(incomplete, ImageSplitterProtocol)


class TestBase64EncoderProtocol:
    """Base64EncoderProtocolのテスト"""

    def test_protocol_exists(self):
        """Base64EncoderProtocolが定義され、runtime_checkableである"""
        from usecases.protocols import Base64EncoderProtocol

        assert not isinstance(object(), Base64EncoderProtocol)

    def test_base64_encoder_implements_protocol(self):
        """Base64Encoderがプロトコルを実装している"""
        from usecases.base64_encoder import Base64Encoder
        from usecases.protocols import Base64EncoderProtocol

        encoder = Base64Encoder()
        assert isinstance(encoder, Base64EncoderProtocol)

    def test_protocol_accepts_full_stub(self):
        """3メソッドを揃えたオブジェクトはプロトコルを満たす"""
        from usecases.protocols import Base64EncoderProtocol

        assert isinstance(_stub(ENCODER_METHODS), Base64EncoderProtocol)

    @pytest.mark.parametrize("missing", ENCODER_METHODS)
    def test_protocol_requires_each_method(self, missing):
        """各メソッドはプロトコルの必須要素（欠けると適合しない）"""
        from usecases.protocols import Base64EncoderProtocol

        incomplete = _stub([m for m in ENCODER_METHODS if m != missing])
        assert not isinstance(incomplete, Base64EncoderProtocol)


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
