#!/usr/bin/env python3
"""
Path Validators - Chain of Responsibility Pattern
==================================================

パス検証のためのValidator Chain実装。

## 使用デザインパターン

### Chain of Responsibility Pattern
複数のValidatorを連鎖させ、いずれかのValidatorが成功するまで
順次検証を行う。

## SOLID原則の実践

### SRP (Single Responsibility Principle)
- 各Validatorは特定の検証ルールのみを担当

### OCP (Open/Closed Principle)
- 新しいValidatorを追加しても既存コードに影響なし

### DIP (Dependency Inversion Principle)
- PathValidator抽象に依存、具象に依存しない

Usage:
    from infrastructure.config.path_validators import (
        PathValidatorChain,
        PluginRootValidator,
        TrustedExternalPathValidator,
    )

    chain = PathValidatorChain([
        PluginRootValidator(),
        TrustedExternalPathValidator(trusted_paths),
    ])

    context = ValidationContext(
        resolved_path=resolved,
        plugin_root=plugin_root,
        trusted_paths=trusted_paths,
        original_setting=base_dir_setting,
    )

    result = chain.validate(context)
    if result.is_valid:
        return result.validated_path
    else:
        raise ConfigError(result.error_message)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

__all__ = [
    "ValidationContext",
    "ValidationResult",
    "PathValidator",
    "PluginRootValidator",
    "TrustedExternalPathValidator",
    "PathValidatorChain",
]


@dataclass
class ValidationContext:
    """パス検証のコンテキスト情報"""

    resolved_path: Path
    plugin_root: Path
    trusted_paths: List[Path] = field(default_factory=list)
    original_setting: str = ""


@dataclass
class ValidationResult:
    """パス検証の結果"""

    is_valid: bool
    validated_path: Optional[Path] = None
    error_message: Optional[str] = None
    validator_name: Optional[str] = None

    @classmethod
    def success(cls, path: Path, validator_name: str) -> "ValidationResult":
        """検証成功の結果を生成"""
        return cls(
            is_valid=True,
            validated_path=path,
            validator_name=validator_name,
        )

    @classmethod
    def failure(cls, message: str, validator_name: str = "") -> "ValidationResult":
        """検証失敗の結果を生成"""
        return cls(
            is_valid=False,
            error_message=message,
            validator_name=validator_name,
        )


class PathValidator(ABC):
    """パスValidator基底クラス（Chain of Responsibility）"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Validator名"""
        pass

    @abstractmethod
    def validate(self, context: ValidationContext) -> Optional[ValidationResult]:
        """
        パスを検証

        Args:
            context: 検証コンテキスト

        Returns:
            ValidationResult if this validator handles the case,
            None if this validator doesn't apply (pass to next)
        """
        pass


class PluginRootValidator(PathValidator):
    """
    Plugin root内のパスを許可するValidator

    plugin_root内のパスであれば常に許可する。
    """

    @property
    def name(self) -> str:
        return "PluginRootValidator"

    def validate(self, context: ValidationContext) -> Optional[ValidationResult]:
        """
        パスがplugin_root内にあるかチェック

        Args:
            context: 検証コンテキスト

        Returns:
            ValidationResult if within plugin_root, None otherwise
        """
        plugin_root_resolved = context.plugin_root.resolve()

        try:
            context.resolved_path.relative_to(plugin_root_resolved)
            return ValidationResult.success(context.resolved_path, self.name)
        except ValueError:
            # plugin_root外 - このValidatorでは処理しない
            return None


class TrustedExternalPathValidator(PathValidator):
    """
    信頼済み外部パス内のパスを許可するValidator

    trusted_external_pathsで明示的に許可されたパス内であれば許可する。
    """

    @property
    def name(self) -> str:
        return "TrustedExternalPathValidator"

    def validate(self, context: ValidationContext) -> Optional[ValidationResult]:
        """
        パスがtrusted_external_paths内にあるかチェック

        Args:
            context: 検証コンテキスト

        Returns:
            ValidationResult if within trusted paths, None otherwise
        """
        if not context.trusted_paths:
            return None  # 信頼済みパスがない場合はスキップ

        for trusted_path in context.trusted_paths:
            try:
                context.resolved_path.relative_to(trusted_path)
                return ValidationResult.success(context.resolved_path, self.name)
            except ValueError:
                continue

        # どの信頼済みパスにも該当しない
        return None


class PathValidatorChain:
    """
    パスValidatorのChain

    複数のValidatorを順次実行し、最初に成功したものの結果を返す。
    どのValidatorも成功しない場合は、エラー結果を返す。

    Attributes:
        validators: 検証に使用するValidatorのリスト

    Example:
        chain = PathValidatorChain([
            PluginRootValidator(),
            TrustedExternalPathValidator(),
        ])
        result = chain.validate(context)
    """

    def __init__(self, validators: List[PathValidator]):
        """
        初期化

        Args:
            validators: Validatorのリスト（順序が重要）
        """
        self._validators = validators

    @property
    def validators(self) -> List[PathValidator]:
        """登録されているValidator一覧"""
        return list(self._validators)

    def validate(self, context: ValidationContext) -> ValidationResult:
        """
        パスを検証（Chain実行）

        各Validatorを順次実行し、最初に成功した結果を返す。
        全Validatorが処理しなかった場合は、エラー結果を返す。

        Args:
            context: 検証コンテキスト

        Returns:
            ValidationResult: 検証結果
        """
        tried_validators: List[str] = []

        for validator in self._validators:
            result = validator.validate(context)
            tried_validators.append(validator.name)

            if result is not None:
                return result

        # どのValidatorも成功しなかった
        return ValidationResult.failure(
            f"Path '{context.original_setting}' (resolves to {context.resolved_path}) "
            f"is not within allowed paths. Tried: {', '.join(tried_validators)}",
            validator_name="PathValidatorChain",
        )

    def add_validator(self, validator: PathValidator) -> None:
        """
        Validatorを追加

        Args:
            validator: 追加するValidator
        """
        self._validators.append(validator)

    def __len__(self) -> int:
        """登録されているValidator数"""
        return len(self._validators)
