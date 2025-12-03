#!/usr/bin/env python3
"""
domain/exceptions.py コンテキスト・実用パターンテスト
=====================================================

DiagnosticContextと実用パターンのテスト。
test_exceptions.py から分割。
"""

from pathlib import Path

import pytest

from domain.exceptions import (
    ConfigError,
    CorruptedDataError,
    DiagnosticContext,
    DigestError,
    EpisodicRAGError,
    FileIOError,
    ValidationError,
)

# =============================================================================
# 実用パターンテスト
# =============================================================================


class TestPracticalUsagePatterns:
    """実用的な使用パターンのテスト"""

    @pytest.mark.unit
    def test_selective_catch(self) -> None:
        """特定の例外を選択的にキャッチ"""
        caught = []

        def raise_various_errors(error_type: str) -> None:
            if error_type == "config":
                raise ConfigError("config")
            elif error_type == "digest":
                raise DigestError("digest")
            elif error_type == "validation":
                raise ValidationError("validation")

        for error_type in ["config", "digest", "validation"]:
            try:
                raise_various_errors(error_type)
            except ConfigError:
                caught.append("config")
            except DigestError:
                caught.append("digest")
            except ValidationError:
                caught.append("validation")

        assert caught == ["config", "digest", "validation"]

    @pytest.mark.unit
    def test_catch_all_episodic_rag_errors(self) -> None:
        """すべてのEpisodicRAGエラーを一括キャッチ"""
        errors = [
            ConfigError("1"),
            DigestError("2"),
            ValidationError("3"),
            FileIOError("4"),
            CorruptedDataError("5"),
        ]

        caught_count = 0
        for error in errors:
            try:
                raise error
            except EpisodicRAGError:
                caught_count += 1

        assert caught_count == 5

    @pytest.mark.unit
    def test_error_message_formatting(self) -> None:
        """エラーメッセージのフォーマット"""
        # ファイルパスを含むエラー
        file_error = FileIOError("Cannot read file: /path/to/config.json")
        assert "/path/to/config.json" in str(file_error)

        # 型情報を含むエラー
        type_error = ValidationError("Expected dict, got <class 'list'>")
        assert "dict" in str(type_error)
        assert "list" in str(type_error)

        # コンテキスト情報を含むエラー
        context_error = ConfigError("Missing required key 'base_dir' in config.json")
        assert "base_dir" in str(context_error)


# =============================================================================
# DiagnosticContext テスト
# =============================================================================


class TestDiagnosticContext:
    """DiagnosticContext のテスト"""

    @pytest.mark.unit
    def test_to_dict_all_fields(self) -> None:
        """全フィールドを設定した場合のto_dict"""
        test_path = Path("/path/to/config.json")
        ctx = DiagnosticContext(
            config_path=test_path,
            current_level="weekly",
            file_count=3,
            threshold=5,
            last_operation="add_files_to_shadow",
            additional_info={"extra": "data"},
        )
        result = ctx.to_dict()

        # Pathは文字列に変換されるが、OS依存のセパレータを使用
        assert result["config_path"] == str(test_path)
        assert result["current_level"] == "weekly"
        assert result["file_count"] == 3
        assert result["threshold"] == 5
        assert result["last_operation"] == "add_files_to_shadow"
        assert result["extra"] == "data"

    @pytest.mark.unit
    def test_to_dict_partial_fields(self) -> None:
        """一部フィールドのみ設定した場合のto_dict"""
        ctx = DiagnosticContext(
            current_level="monthly",
            file_count=10,
        )
        result = ctx.to_dict()

        assert "current_level" in result
        assert "file_count" in result
        assert "config_path" not in result
        assert "threshold" not in result
        assert "last_operation" not in result

    @pytest.mark.unit
    def test_to_dict_empty(self) -> None:
        """空のコンテキストのto_dict"""
        ctx = DiagnosticContext()
        result = ctx.to_dict()
        assert result == {}

    @pytest.mark.unit
    def test_str_representation(self) -> None:
        """__str__の文字列表現"""
        ctx = DiagnosticContext(
            current_level="weekly",
            file_count=3,
            threshold=5,
        )
        result = str(ctx)

        assert "current_level=weekly" in result
        assert "file_count=3" in result
        assert "threshold=5" in result

    @pytest.mark.unit
    def test_str_empty_context(self) -> None:
        """空のコンテキストの__str__"""
        ctx = DiagnosticContext()
        assert str(ctx) == ""

    @pytest.mark.unit
    def test_additional_info_merged(self) -> None:
        """additional_infoがto_dictにマージされる"""
        ctx = DiagnosticContext(
            current_level="weekly",
            additional_info={"key1": "value1", "key2": 42},
        )
        result = ctx.to_dict()

        assert result["current_level"] == "weekly"
        assert result["key1"] == "value1"
        assert result["key2"] == 42


# =============================================================================
# EpisodicRAGError コンテキスト付きテスト
# =============================================================================


class TestEpisodicRAGErrorWithContext:
    """EpisodicRAGError のコンテキスト付きテスト"""

    @pytest.mark.unit
    def test_str_with_context(self) -> None:
        """コンテキスト付きエラーの__str__"""
        ctx = DiagnosticContext(
            current_level="weekly",
            file_count=3,
        )
        error = EpisodicRAGError("Processing failed", context=ctx)
        result = str(error)

        assert "Processing failed" in result
        assert "[Context:" in result
        assert "current_level=weekly" in result
        assert "file_count=3" in result

    @pytest.mark.unit
    def test_str_without_context(self) -> None:
        """コンテキストなしエラーの__str__"""
        error = EpisodicRAGError("Simple error")
        result = str(error)

        assert result == "Simple error"
        assert "[Context:" not in result

    @pytest.mark.unit
    def test_str_with_empty_context(self) -> None:
        """空のコンテキストを持つエラーの__str__"""
        ctx = DiagnosticContext()
        error = EpisodicRAGError("Error with empty context", context=ctx)
        result = str(error)

        # 空のコンテキストは表示されない
        assert result == "Error with empty context"

    @pytest.mark.unit
    def test_context_attribute_accessible(self) -> None:
        """context属性にアクセスできる"""
        ctx = DiagnosticContext(current_level="monthly")
        error = EpisodicRAGError("Error", context=ctx)

        assert error.context is ctx
        assert error.context.current_level == "monthly"

    @pytest.mark.unit
    def test_subclass_with_context(self) -> None:
        """サブクラスでもコンテキストが機能する"""
        ctx = DiagnosticContext(
            current_level="weekly",
            threshold=5,
        )
        error = DigestError("Digest processing failed", context=ctx)
        result = str(error)

        assert "Digest processing failed" in result
        assert "current_level=weekly" in result
        assert "threshold=5" in result

    @pytest.mark.unit
    def test_context_with_path(self) -> None:
        """Pathを含むコンテキスト"""
        test_path = Path("/home/user/config.json")
        ctx = DiagnosticContext(
            config_path=test_path,
        )
        error = ConfigError("Config error", context=ctx)
        result = str(error)

        # OS依存のパス形式を考慮
        assert f"config_path={test_path}" in result
