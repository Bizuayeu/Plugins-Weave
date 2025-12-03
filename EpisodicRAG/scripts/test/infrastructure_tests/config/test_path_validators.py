#!/usr/bin/env python3
"""
Path Validators テスト
=======================

Chain of Responsibility Pattern 実装のテスト。
- 個別Validator
- Validator Chain
"""

from pathlib import Path

import pytest

from infrastructure.config import (
    PathValidator,
    PathValidatorChain,
    PluginRootValidator,
    TrustedExternalPathValidator,
    ValidationContext,
    ValidationResult,
)


# =============================================================================
# ValidationResult Tests
# =============================================================================


class TestValidationResult:
    """ValidationResult dataclass tests"""

    @pytest.mark.unit
    def test_create_success_result(self) -> None:

        """Create success result"""
        path = Path("/test/path")
        result = ValidationResult.success(path, "TestValidator")

        assert result.is_valid is True
        assert result.validated_path == path
        assert result.validator_name == "TestValidator"
        assert result.error_message is None

    @pytest.mark.unit
    def test_create_failure_result(self) -> None:

        """Create failure result"""
        result = ValidationResult.failure("Test error", "TestValidator")

        assert result.is_valid is False
        assert result.validated_path is None
        assert result.error_message == "Test error"
        assert result.validator_name == "TestValidator"


# =============================================================================
# ValidationContext Tests
# =============================================================================


class TestValidationContext:
    """ValidationContext dataclass tests"""

    @pytest.mark.unit
    def test_create_context(self) -> None:

        """Create context with all fields"""
        context = ValidationContext(
            resolved_path=Path("/test/resolved"),
            plugin_root=Path("/test/plugin"),
            trusted_paths=[Path("/trusted/path1"), Path("/trusted/path2")],
            original_setting="./relative",
        )

        assert context.resolved_path == Path("/test/resolved")
        assert context.plugin_root == Path("/test/plugin")
        assert len(context.trusted_paths) == 2
        assert context.original_setting == "./relative"

    @pytest.mark.unit
    def test_context_defaults(self) -> None:

        """Context has sensible defaults"""
        context = ValidationContext(
            resolved_path=Path("/test"),
            plugin_root=Path("/plugin"),
        )

        assert context.trusted_paths == []
        assert context.original_setting == ""


# =============================================================================
# PluginRootValidator Tests
# =============================================================================


class TestPluginRootValidator:
    """PluginRootValidator tests"""

    @pytest.fixture
    def validator(self):

        """Create validator instance"""
        return PluginRootValidator()

    @pytest.mark.unit
    def test_validator_name(self, validator) -> None:

        """Validator has correct name"""
        assert validator.name == "PluginRootValidator"

    @pytest.mark.unit
    def test_validates_path_within_plugin_root(self, validator, tmp_path: Path) -> None:

        """Validates path within plugin root"""
        plugin_root = tmp_path / "plugin"
        plugin_root.mkdir()
        resolved_path = plugin_root / "subdir" / "file.txt"

        context = ValidationContext(
            resolved_path=resolved_path,
            plugin_root=plugin_root,
        )

        result = validator.validate(context)

        assert result is not None
        assert result.is_valid is True
        assert result.validated_path == resolved_path
        assert result.validator_name == "PluginRootValidator"

    @pytest.mark.unit
    def test_returns_none_for_path_outside_plugin_root(self, validator, tmp_path: Path) -> None:

        """Returns None for path outside plugin root"""
        plugin_root = tmp_path / "plugin"
        plugin_root.mkdir()
        outside_path = tmp_path / "outside" / "file.txt"

        context = ValidationContext(
            resolved_path=outside_path,
            plugin_root=plugin_root,
        )

        result = validator.validate(context)

        assert result is None  # Not handled by this validator


# =============================================================================
# TrustedExternalPathValidator Tests
# =============================================================================


class TestTrustedExternalPathValidator:
    """TrustedExternalPathValidator tests"""

    @pytest.fixture
    def validator(self):

        """Create validator instance"""
        return TrustedExternalPathValidator()

    @pytest.mark.unit
    def test_validator_name(self, validator) -> None:

        """Validator has correct name"""
        assert validator.name == "TrustedExternalPathValidator"

    @pytest.mark.unit
    def test_validates_path_within_trusted_paths(self, validator, tmp_path: Path) -> None:

        """Validates path within trusted paths"""
        trusted_path = tmp_path / "trusted"
        trusted_path.mkdir()
        resolved_path = trusted_path / "subdir" / "file.txt"

        context = ValidationContext(
            resolved_path=resolved_path,
            plugin_root=tmp_path / "plugin",
            trusted_paths=[trusted_path],
        )

        result = validator.validate(context)

        assert result is not None
        assert result.is_valid is True
        assert result.validated_path == resolved_path
        assert result.validator_name == "TrustedExternalPathValidator"

    @pytest.mark.unit
    def test_returns_none_for_path_outside_trusted_paths(self, validator, tmp_path: Path) -> None:

        """Returns None for path outside trusted paths"""
        trusted_path = tmp_path / "trusted"
        trusted_path.mkdir()
        outside_path = tmp_path / "untrusted" / "file.txt"

        context = ValidationContext(
            resolved_path=outside_path,
            plugin_root=tmp_path / "plugin",
            trusted_paths=[trusted_path],
        )

        result = validator.validate(context)

        assert result is None

    @pytest.mark.unit
    def test_returns_none_when_no_trusted_paths(self, validator, tmp_path: Path) -> None:

        """Returns None when no trusted paths configured"""
        context = ValidationContext(
            resolved_path=tmp_path / "any",
            plugin_root=tmp_path / "plugin",
            trusted_paths=[],
        )

        result = validator.validate(context)

        assert result is None

    @pytest.mark.unit
    def test_checks_multiple_trusted_paths(self, validator, tmp_path: Path) -> None:

        """Checks all trusted paths until one matches"""
        trusted1 = tmp_path / "trusted1"
        trusted2 = tmp_path / "trusted2"
        trusted1.mkdir()
        trusted2.mkdir()
        resolved_path = trusted2 / "subdir" / "file.txt"

        context = ValidationContext(
            resolved_path=resolved_path,
            plugin_root=tmp_path / "plugin",
            trusted_paths=[trusted1, trusted2],
        )

        result = validator.validate(context)

        assert result is not None
        assert result.is_valid is True


# =============================================================================
# PathValidatorChain Tests
# =============================================================================


class TestPathValidatorChain:
    """PathValidatorChain tests"""

    @pytest.mark.unit
    def test_chain_with_single_validator(self, tmp_path: Path) -> None:

        """Chain with single validator"""
        plugin_root = tmp_path / "plugin"
        plugin_root.mkdir()
        resolved_path = plugin_root / "data" / "file.txt"

        chain = PathValidatorChain([PluginRootValidator()])
        context = ValidationContext(
            resolved_path=resolved_path,
            plugin_root=plugin_root,
        )

        result = chain.validate(context)

        assert result.is_valid is True
        assert result.validated_path == resolved_path

    @pytest.mark.unit
    def test_chain_tries_validators_in_order(self, tmp_path: Path) -> None:

        """Chain tries validators in order"""
        plugin_root = tmp_path / "plugin"
        trusted_path = tmp_path / "trusted"
        plugin_root.mkdir()
        trusted_path.mkdir()

        # Path is within trusted, not plugin_root
        resolved_path = trusted_path / "data" / "file.txt"

        chain = PathValidatorChain([
            PluginRootValidator(),
            TrustedExternalPathValidator(),
        ])
        context = ValidationContext(
            resolved_path=resolved_path,
            plugin_root=plugin_root,
            trusted_paths=[trusted_path],
        )

        result = chain.validate(context)

        assert result.is_valid is True
        assert result.validator_name == "TrustedExternalPathValidator"

    @pytest.mark.unit
    def test_chain_returns_failure_when_no_validator_matches(self, tmp_path: Path) -> None:

        """Chain returns failure when no validator matches"""
        plugin_root = tmp_path / "plugin"
        trusted_path = tmp_path / "trusted"
        outside_path = tmp_path / "untrusted" / "file.txt"
        plugin_root.mkdir()
        trusted_path.mkdir()

        chain = PathValidatorChain([
            PluginRootValidator(),
            TrustedExternalPathValidator(),
        ])
        context = ValidationContext(
            resolved_path=outside_path,
            plugin_root=plugin_root,
            trusted_paths=[trusted_path],
            original_setting="./untrusted/file.txt",
        )

        result = chain.validate(context)

        assert result.is_valid is False
        assert "not within allowed paths" in result.error_message
        assert "PluginRootValidator" in result.error_message
        assert "TrustedExternalPathValidator" in result.error_message

    @pytest.mark.unit
    def test_chain_length(self) -> None:

        """Chain reports correct length"""
        chain = PathValidatorChain([
            PluginRootValidator(),
            TrustedExternalPathValidator(),
        ])

        assert len(chain) == 2

    @pytest.mark.unit
    def test_chain_add_validator(self) -> None:

        """Can add validators to chain"""
        chain = PathValidatorChain([PluginRootValidator()])
        assert len(chain) == 1

        chain.add_validator(TrustedExternalPathValidator())
        assert len(chain) == 2

    @pytest.mark.unit
    def test_chain_validators_property(self) -> None:

        """validators property returns list of validators"""
        validator1 = PluginRootValidator()
        validator2 = TrustedExternalPathValidator()
        chain = PathValidatorChain([validator1, validator2])

        validators = chain.validators
        assert len(validators) == 2
        assert validators[0] is validator1
        assert validators[1] is validator2


# =============================================================================
# Import Tests
# =============================================================================


class TestPathValidatorImports:
    """Path validator import path tests"""

    @pytest.mark.unit
    def test_import_from_package(self) -> None:

        """Import from infrastructure.config package"""
        from infrastructure.config import (
            PathValidator,
            PathValidatorChain,
            PluginRootValidator,
            TrustedExternalPathValidator,
            ValidationContext,
            ValidationResult,
        )

        assert PathValidator is not None
        assert PathValidatorChain is not None
        assert PluginRootValidator is not None
        assert TrustedExternalPathValidator is not None
        assert ValidationContext is not None
        assert ValidationResult is not None

    @pytest.mark.unit
    def test_import_from_module(self) -> None:

        """Import from infrastructure.config.path_validators module"""
        from infrastructure.config.path_validators import (
            PathValidator,
            PathValidatorChain,
            PluginRootValidator,
            TrustedExternalPathValidator,
            ValidationContext,
            ValidationResult,
        )

        assert PathValidator is not None
        assert PathValidatorChain is not None
        assert PluginRootValidator is not None
        assert TrustedExternalPathValidator is not None
        assert ValidationContext is not None
        assert ValidationResult is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
