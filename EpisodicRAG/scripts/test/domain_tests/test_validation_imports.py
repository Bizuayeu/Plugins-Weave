#!/usr/bin/env python3
"""
Validation 後方互換性テスト
===========================

バリデーション統合後も、既存のすべてのインポートパスが動作することを確認。
"""

import pytest


class TestValidationImportBackwardCompatibility:
    """既存のインポートパスが動作することを確認"""

    def test_import_from_domain_validation(self) -> None:
        """domain.validation からインポート可能（後方互換性）"""
        from domain.validation import collect_type_error, validate_type

        assert callable(validate_type)
        assert callable(collect_type_error)

    def test_import_from_domain_validation_helpers(self) -> None:
        """domain.validation_helpers からインポート可能（後方互換性）"""
        from domain.validation_helpers import (
            collect_list_element_errors,
            validate_dict_has_keys,
            validate_dict_key_type,
            validate_list_not_empty,
        )

        assert callable(validate_list_not_empty)
        assert callable(validate_dict_has_keys)
        assert callable(validate_dict_key_type)
        assert callable(collect_list_element_errors)

    def test_import_from_domain_validators(self) -> None:
        """domain.validators からインポート可能"""
        from domain.validators import (
            ensure_not_none,
            get_dict_or_empty,
            get_list_or_empty,
            get_or_default,
            is_valid_dict,
            is_valid_list,
            is_valid_overall_digest,
            is_valid_type,
        )

        assert callable(is_valid_overall_digest)
        assert callable(ensure_not_none)
        assert callable(is_valid_type)
        assert callable(get_or_default)
        assert callable(is_valid_dict)
        assert callable(is_valid_list)
        assert callable(get_dict_or_empty)
        assert callable(get_list_or_empty)


class TestValidatorsSubmoduleImports:
    """サブモジュールからの直接インポートが動作することを確認"""

    def test_import_from_type_validators(self) -> None:
        """domain.validators.type_validators からインポート可能"""
        from domain.validators.type_validators import is_valid_dict, is_valid_list

        assert callable(is_valid_dict)
        assert callable(is_valid_list)

    def test_import_from_digest_validators(self) -> None:
        """domain.validators.digest_validators からインポート可能"""
        from domain.validators.digest_validators import is_valid_overall_digest

        assert callable(is_valid_overall_digest)

    def test_import_from_runtime_checks(self) -> None:
        """domain.validators.runtime_checks からインポート可能"""
        from domain.validators.runtime_checks import ensure_not_none

        assert callable(ensure_not_none)

    def test_import_from_helpers(self) -> None:
        """domain.validators.helpers からインポート可能"""
        from domain.validators.helpers import (
            collect_type_error,
            validate_list_not_empty,
            validate_type,
        )

        assert callable(validate_type)
        assert callable(validate_list_not_empty)
        assert callable(collect_type_error)


class TestValidatorsUnifiedImport:
    """統合後の新しいインポートパスが動作することを確認"""

    def test_import_all_from_domain_validators(self) -> None:
        """domain.validators から全関数をインポート可能"""
        from domain.validators import (
            # Helpers (error collectors)
            collect_list_element_errors,
            collect_type_error,
            # Business validators
            ensure_not_none,
            # Type validators (non-throwing)
            get_dict_or_empty,
            get_list_or_empty,
            get_or_default,
            get_str_or_empty,
            is_valid_dict,
            is_valid_int,
            is_valid_list,
            is_valid_overall_digest,
            is_valid_str,
            is_valid_type,
            # Helpers (throwing validators)
            validate_dict_has_keys,
            validate_dict_key_type,
            validate_list_not_empty,
            validate_type,
        )

        # Type validators
        assert callable(is_valid_type)
        assert callable(get_or_default)
        assert callable(is_valid_dict)
        assert callable(is_valid_list)
        assert callable(is_valid_str)
        assert callable(is_valid_int)
        assert callable(get_dict_or_empty)
        assert callable(get_list_or_empty)
        assert callable(get_str_or_empty)

        # Business validators
        assert callable(is_valid_overall_digest)
        assert callable(ensure_not_none)

        # Helpers (throwing)
        assert callable(validate_type)
        assert callable(validate_list_not_empty)
        assert callable(validate_dict_has_keys)
        assert callable(validate_dict_key_type)

        # Helpers (collectors)
        assert callable(collect_type_error)
        assert callable(collect_list_element_errors)


class TestValidatorsUsability:
    """バリデーション関数が正しく動作することを確認"""

    def test_is_valid_dict_works(self) -> None:
        """is_valid_dict が正しく動作"""
        from domain.validators import is_valid_dict

        assert is_valid_dict({"key": "value"}) is True
        assert is_valid_dict([1, 2, 3]) is False
        assert is_valid_dict(None) is False

    def test_is_valid_list_works(self) -> None:
        """is_valid_list が正しく動作"""
        from domain.validators import is_valid_list

        assert is_valid_list([1, 2, 3]) is True
        assert is_valid_list({"key": "value"}) is False
        assert is_valid_list(None) is False

    def test_is_valid_overall_digest_works(self) -> None:
        """is_valid_overall_digest が正しく動作"""
        from domain.validators import is_valid_overall_digest

        valid_digest = {"source_files": ["file1.txt"]}
        empty_digest = {"source_files": []}
        invalid_digest = {"other_key": "value"}

        assert is_valid_overall_digest(valid_digest) is True
        assert is_valid_overall_digest(empty_digest) is False
        assert is_valid_overall_digest(invalid_digest) is False

    def test_ensure_not_none_works(self) -> None:
        """ensure_not_none が正しく動作"""
        from domain.exceptions import ValidationError
        from domain.validators import ensure_not_none

        result = ensure_not_none("value", "test")
        assert result == "value"

        with pytest.raises(ValidationError):
            ensure_not_none(None, "test")

    def test_validate_type_works(self) -> None:
        """validate_type が正しく動作"""
        from domain.exceptions import ValidationError
        from domain.validators import validate_type

        result = validate_type({"key": "value"}, dict, "test", "dict")
        assert result == {"key": "value"}

        with pytest.raises(ValidationError):
            validate_type("string", dict, "test", "dict")

    def test_collect_type_error_works(self) -> None:
        """collect_type_error が正しく動作"""
        from domain.validators import collect_type_error

        errors: list[str] = []
        collect_type_error("string", str, "test_key", errors)
        assert len(errors) == 0  # Valid type

        collect_type_error(123, str, "test_key", errors)
        assert len(errors) == 1  # Invalid type
        assert "test_key" in errors[0]
