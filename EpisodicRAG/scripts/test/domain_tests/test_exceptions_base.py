#!/usr/bin/env python3
"""
domain/exceptions.py 基本例外テスト
===================================

例外階層と各例外クラスの基本テスト。
test_exceptions.py から分割。
"""

import pytest

from domain.exceptions import (
    ConfigError,
    CorruptedDataError,
    DigestError,
    EpisodicRAGError,
    FileIOError,
    ValidationError,
)

# =============================================================================
# 例外階層テスト
# =============================================================================


class TestExceptionHierarchy:
    """例外階層の継承関係テスト"""

    @pytest.mark.unit
    def test_episodic_rag_error_inherits_from_exception(self) -> None:

        """EpisodicRAGError は Exception を継承"""
        assert issubclass(EpisodicRAGError, Exception)

    @pytest.mark.unit
    def test_config_error_inherits_from_episodic_rag_error(self) -> None:

        """ConfigError は EpisodicRAGError を継承"""
        assert issubclass(ConfigError, EpisodicRAGError)

    @pytest.mark.unit
    def test_digest_error_inherits_from_episodic_rag_error(self) -> None:

        """DigestError は EpisodicRAGError を継承"""
        assert issubclass(DigestError, EpisodicRAGError)

    @pytest.mark.unit
    def test_validation_error_inherits_from_episodic_rag_error(self) -> None:

        """ValidationError は EpisodicRAGError を継承"""
        assert issubclass(ValidationError, EpisodicRAGError)

    @pytest.mark.unit
    def test_file_io_error_inherits_from_episodic_rag_error(self) -> None:

        """FileIOError は EpisodicRAGError を継承"""
        assert issubclass(FileIOError, EpisodicRAGError)

    @pytest.mark.unit
    def test_corrupted_data_error_inherits_from_episodic_rag_error(self) -> None:

        """CorruptedDataError は EpisodicRAGError を継承"""
        assert issubclass(CorruptedDataError, EpisodicRAGError)


# =============================================================================
# EpisodicRAGError テスト
# =============================================================================


class TestEpisodicRAGError:
    """EpisodicRAGError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self) -> None:

        """例外を発生させることができる"""
        with pytest.raises(EpisodicRAGError):
            raise EpisodicRAGError("Test error")

    @pytest.mark.unit
    def test_message_is_preserved(self) -> None:

        """エラーメッセージが保持される"""
        try:
            raise EpisodicRAGError("Test message")
        except EpisodicRAGError as e:
            assert str(e) == "Test message"

    @pytest.mark.unit
    def test_can_catch_all_subclasses(self) -> None:

        """すべてのサブクラスをキャッチできる"""
        errors = [
            ConfigError("config"),
            DigestError("digest"),
            ValidationError("validation"),
            FileIOError("fileio"),
            CorruptedDataError("corrupted"),
        ]
        for error in errors:
            with pytest.raises(EpisodicRAGError):
                raise error


# =============================================================================
# ConfigError テスト
# =============================================================================


class TestConfigError:
    """ConfigError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self) -> None:

        """例外を発生させることができる"""
        with pytest.raises(ConfigError):
            raise ConfigError("Config not found")

    @pytest.mark.unit
    def test_message_is_preserved(self) -> None:

        """エラーメッセージが保持される"""
        try:
            raise ConfigError("Invalid config.json format")
        except ConfigError as e:
            assert "Invalid config.json format" in str(e)

    @pytest.mark.unit
    def test_can_be_caught_as_episodic_rag_error(self) -> None:

        """EpisodicRAGError としてキャッチできる"""
        with pytest.raises(EpisodicRAGError):
            raise ConfigError("Test")

    @pytest.mark.unit
    def test_unicode_message(self) -> None:

        """Unicode メッセージを扱える"""
        try:
            raise ConfigError("設定ファイルが見つかりません")
        except ConfigError as e:
            assert "設定ファイルが見つかりません" in str(e)


# =============================================================================
# DigestError テスト
# =============================================================================


class TestDigestError:
    """DigestError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self) -> None:

        """例外を発生させることができる"""
        with pytest.raises(DigestError):
            raise DigestError("Digest generation failed")

    @pytest.mark.unit
    def test_message_is_preserved(self) -> None:

        """エラーメッセージが保持される"""
        try:
            raise DigestError("Shadow digest load failed")
        except DigestError as e:
            assert "Shadow digest load failed" in str(e)


# =============================================================================
# ValidationError テスト
# =============================================================================


class TestValidationError:
    """ValidationError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self) -> None:

        """例外を発生させることができる"""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid data type")

    @pytest.mark.unit
    def test_message_is_preserved(self) -> None:

        """エラーメッセージが保持される"""
        try:
            raise ValidationError("source_files must be a list")
        except ValidationError as e:
            assert "source_files must be a list" in str(e)

    @pytest.mark.unit
    def test_can_include_context(self) -> None:

        """コンテキスト情報を含められる"""
        try:
            raise ValidationError("Expected dict, got list in 'overall_digest'")
        except ValidationError as e:
            assert "overall_digest" in str(e)


# =============================================================================
# FileIOError テスト
# =============================================================================


class TestFileIOError:
    """FileIOError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self) -> None:

        """例外を発生させることができる"""
        with pytest.raises(FileIOError):
            raise FileIOError("File not found")

    @pytest.mark.unit
    def test_message_is_preserved(self) -> None:

        """エラーメッセージが保持される"""
        try:
            raise FileIOError("Cannot write to /path/to/file.json")
        except FileIOError as e:
            assert "Cannot write to" in str(e)

    @pytest.mark.unit
    def test_distinct_from_builtin_ioerror(self) -> None:

        """組み込みのIOErrorとは別"""
        # FileIOError は EpisodicRAGError を継承しているため、
        # 組み込みの IOError/OSError とは異なる
        try:
            raise FileIOError("Test")
        except IOError:
            pytest.fail("Should not be caught as IOError")
        except EpisodicRAGError:
            pass  # Expected


# =============================================================================
# CorruptedDataError テスト
# =============================================================================


class TestCorruptedDataError:
    """CorruptedDataError のテスト"""

    @pytest.mark.unit
    def test_can_be_raised(self) -> None:

        """例外を発生させることができる"""
        with pytest.raises(CorruptedDataError):
            raise CorruptedDataError("JSON file corrupted")

    @pytest.mark.unit
    def test_message_is_preserved(self) -> None:

        """エラーメッセージが保持される"""
        try:
            raise CorruptedDataError("Integrity check failed for GrandDigest.txt")
        except CorruptedDataError as e:
            assert "Integrity check failed" in str(e)


# =============================================================================
# 例外チェーンテスト
# =============================================================================


class TestExceptionChaining:
    """例外チェーン（from e）のテスト"""

    @pytest.mark.unit
    def test_config_error_chaining(self) -> None:

        """ConfigError で例外チェーンが機能する"""
        original = ValueError("Original error")
        try:
            try:
                raise original
            except ValueError as e:
                raise ConfigError("Config error") from e
        except ConfigError as e:
            assert e.__cause__ is original

    @pytest.mark.unit
    def test_file_io_error_chaining(self) -> None:

        """FileIOError で例外チェーンが機能する"""
        original = OSError("Permission denied")
        try:
            try:
                raise original
            except OSError as e:
                raise FileIOError(f"Cannot read file: {e}") from e
        except FileIOError as e:
            assert e.__cause__ is original

    @pytest.mark.unit
    def test_corrupted_data_error_chaining(self) -> None:

        """CorruptedDataError で例外チェーンが機能する"""
        import json

        original = json.JSONDecodeError("Expecting value", "", 0)
        try:
            try:
                raise original
            except json.JSONDecodeError as e:
                raise CorruptedDataError(f"Invalid JSON: {e}") from e
        except CorruptedDataError as e:
            assert e.__cause__ is original

    @pytest.mark.unit
    def test_chain_preserves_traceback(self) -> None:

        """例外チェーンでトレースバックが保持される"""
        import traceback

        try:
            try:
                raise ValueError("inner")
            except ValueError as e:
                raise ConfigError("outer") from e
        except ConfigError as e:
            tb = traceback.format_exception(type(e), e, e.__traceback__)
            tb_str = "".join(tb)
            assert "ValueError" in tb_str
            assert "inner" in tb_str
            assert "ConfigError" in tb_str
            assert "outer" in tb_str
