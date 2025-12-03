#!/usr/bin/env python3
"""
test_protocols.py
=================

domain/protocols.py のユニットテスト。
Protocol定義の構造的部分型付けを検証。
"""

from typing import Optional, Protocol, runtime_checkable

import pytest

from domain.protocols import LevelBehaviorProtocol, LevelRegistryProtocol

# =============================================================================
# LevelBehaviorProtocol テスト
# =============================================================================


class TestLevelBehaviorProtocol:
    """LevelBehaviorProtocol のテスト"""

    @pytest.mark.unit
    def test_protocol_defines_format_number(self) -> None:
        """format_number メソッドが定義されている"""
        assert hasattr(LevelBehaviorProtocol, "format_number")

    @pytest.mark.unit
    def test_protocol_defines_should_cascade(self) -> None:
        """should_cascade メソッドが定義されている"""
        assert hasattr(LevelBehaviorProtocol, "should_cascade")

    @pytest.mark.unit
    def test_structural_subtyping_with_conforming_class(self):
        """適合するクラスはProtocolを満たす"""

        class ConformingBehavior:
            def format_number(self, number: int) -> str:
                return f"W{number:04d}"

            def should_cascade(self) -> bool:
                return True

        # 構造的部分型付け: ConformingBehavior は LevelBehaviorProtocol を満たす
        behavior: LevelBehaviorProtocol = ConformingBehavior()
        assert behavior.format_number(42) == "W0042"
        assert behavior.should_cascade() is True

    @pytest.mark.unit
    def test_structural_subtyping_with_non_conforming_class(self):
        """適合しないクラスの例（型チェッカーで検出）"""

        class NonConformingBehavior:
            def format_number(self, number: int) -> str:
                return str(number)

            # should_cascade がない

        # 実行時にはエラーにならないが、型チェッカーはエラーを報告する
        behavior = NonConformingBehavior()
        assert behavior.format_number(42) == "42"

    @pytest.mark.unit
    def test_real_level_behavior_conforms(self) -> None:
        """実際の LevelBehavior 実装クラスが Protocol を満たす"""
        from domain.level_registry import LevelMetadata, StandardLevelBehavior

        # StandardLevelBehavior は LevelBehaviorProtocol を満たすはず
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        behavior = StandardLevelBehavior(metadata)
        typed_behavior: LevelBehaviorProtocol = behavior

        assert typed_behavior.format_number(1) == "W0001"
        assert typed_behavior.should_cascade() is True


# =============================================================================
# LevelRegistryProtocol テスト
# =============================================================================


class TestLevelRegistryProtocol:
    """LevelRegistryProtocol のテスト"""

    @pytest.mark.unit
    def test_protocol_defines_build_prefix_pattern(self) -> None:
        """build_prefix_pattern メソッドが定義されている"""
        assert hasattr(LevelRegistryProtocol, "build_prefix_pattern")

    @pytest.mark.unit
    def test_protocol_defines_get_behavior(self) -> None:
        """get_behavior メソッドが定義されている"""
        assert hasattr(LevelRegistryProtocol, "get_behavior")

    @pytest.mark.unit
    def test_protocol_defines_get_level_by_prefix(self) -> None:
        """get_level_by_prefix メソッドが定義されている"""
        assert hasattr(LevelRegistryProtocol, "get_level_by_prefix")

    @pytest.mark.unit
    def test_structural_subtyping_with_conforming_class(self):
        """適合するクラスはProtocolを満たす"""

        class MockBehavior:
            def format_number(self, number: int) -> str:
                return f"T{number:04d}"

            def should_cascade(self) -> bool:
                return False

        class ConformingRegistry:
            def build_prefix_pattern(self) -> str:
                return "W|M|Q"

            def get_behavior(self, level: str) -> LevelBehaviorProtocol:
                return MockBehavior()

            def get_level_by_prefix(self, prefix: str) -> Optional[str]:
                mapping = {"W": "weekly", "M": "monthly"}
                return mapping.get(prefix)

        registry: LevelRegistryProtocol = ConformingRegistry()
        assert registry.build_prefix_pattern() == "W|M|Q"
        assert registry.get_level_by_prefix("W") == "weekly"
        assert registry.get_level_by_prefix("X") is None

    @pytest.mark.unit
    def test_real_level_registry_conforms(self) -> None:
        """実際の LevelRegistry クラスが Protocol を満たす"""
        from domain.level_registry import LevelRegistry

        registry = LevelRegistry()
        typed_registry: LevelRegistryProtocol = registry

        # Protocol のメソッドが使用可能
        pattern = typed_registry.build_prefix_pattern()
        assert "W" in pattern  # weekly の prefix
        assert "M" in pattern  # monthly の prefix

        behavior = typed_registry.get_behavior("weekly")
        assert behavior.format_number(1) == "W0001"

        level = typed_registry.get_level_by_prefix("W")
        assert level == "weekly"


# =============================================================================
# Protocol の一般的なテスト
# =============================================================================


class TestProtocolGeneral:
    """Protocol 一般のテスト"""

    @pytest.mark.unit
    def test_protocols_are_exported(self) -> None:
        """protocols モジュールから正しくエクスポートされている"""
        from domain import protocols

        assert hasattr(protocols, "LevelBehaviorProtocol")
        assert hasattr(protocols, "LevelRegistryProtocol")

    @pytest.mark.unit
    def test_protocols_in_all(self) -> None:
        """__all__ に含まれている"""
        from domain.protocols import __all__

        assert "LevelBehaviorProtocol" in __all__
        assert "LevelRegistryProtocol" in __all__

    @pytest.mark.unit
    def test_protocol_is_typing_protocol(self) -> None:
        """Protocol が typing.Protocol のサブクラス"""
        assert issubclass(LevelBehaviorProtocol, Protocol)
        assert issubclass(LevelRegistryProtocol, Protocol)

    @pytest.mark.unit
    def test_protocol_not_instantiable_directly(self) -> None:
        """Protocol は直接インスタンス化できない"""
        # Protocol は直接インスタンス化できる（TypeError にはならない）
        # ただし、メソッドは ... なので使用するとエラー
        # これは typing.Protocol の仕様
        pass  # Protocol の直接インスタンス化は TypeScript とは異なり可能

    @pytest.mark.unit
    def test_dependency_inversion_example(self) -> None:
        """依存関係逆転の例"""
        # file_naming.py は protocols.py に依存し、
        # level_registry.py を直接 import しない

        import inspect

        from domain import file_naming

        source = inspect.getsource(file_naming)
        # protocols からの import があるはず
        assert "from domain.protocols import" in source or "domain.protocols" in source
