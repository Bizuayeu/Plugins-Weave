#!/usr/bin/env python3
"""
Level Behaviors Unit Tests
==========================

Tests for domain/level_behaviors.py

Strategy Pattern implementation for level-specific behaviors.
"""

import pytest

from domain.level_behaviors import LevelBehavior, LoopLevelBehavior, StandardLevelBehavior
from domain.level_metadata import LevelMetadata

# =============================================================================
# LevelBehavior Abstract Class Tests
# =============================================================================


class TestLevelBehaviorAbstract:
    """LevelBehavior abstract class tests"""

    def test_cannot_instantiate_directly(self) -> None:

        """Cannot instantiate abstract LevelBehavior directly"""
        with pytest.raises(TypeError):
            LevelBehavior()

    def test_requires_format_number_implementation(self):

        """Subclass must implement format_number"""

        class IncompleteBehavior(LevelBehavior):
            def should_cascade(self):

                return True

        with pytest.raises(TypeError):
            IncompleteBehavior()

    def test_requires_should_cascade_implementation(self):

        """Subclass must implement should_cascade"""

        class IncompleteBehavior(LevelBehavior):
            def format_number(self, number):

                return str(number)

        with pytest.raises(TypeError):
            IncompleteBehavior()


# =============================================================================
# StandardLevelBehavior Tests
# =============================================================================


class TestStandardLevelBehaviorInit:
    """StandardLevelBehavior initialization tests"""

    def test_init_with_metadata(self) -> None:

        """Initializes with LevelMetadata"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        behavior = StandardLevelBehavior(metadata)

        assert behavior.metadata is metadata

    def test_stores_metadata_reference(self) -> None:

        """Stores reference to metadata"""
        metadata = LevelMetadata(
            name="monthly", prefix="M", digits=4, dir="2_Monthly", source="weekly", next_level=None
        )
        behavior = StandardLevelBehavior(metadata)

        assert behavior.metadata.name == "monthly"
        assert behavior.metadata.prefix == "M"


class TestStandardLevelBehaviorFormatNumber:
    """StandardLevelBehavior.format_number() tests"""

    @pytest.fixture
    def weekly_behavior(self):

        """Weekly level behavior"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        return StandardLevelBehavior(metadata)

    @pytest.fixture
    def monthly_behavior(self):

        """Monthly level behavior with different digits"""
        metadata = LevelMetadata(
            name="monthly", prefix="M", digits=3, dir="2_Monthly", source="weekly", next_level=None
        )
        return StandardLevelBehavior(metadata)

    def test_formats_with_prefix_and_padding(self, weekly_behavior) -> None:

        """Formats with prefix and zero padding"""
        result = weekly_behavior.format_number(1)
        assert result == "W0001"

    def test_formats_larger_number(self, weekly_behavior) -> None:

        """Formats larger numbers correctly"""
        result = weekly_behavior.format_number(42)
        assert result == "W0042"

    def test_formats_max_number(self, weekly_behavior) -> None:

        """Formats maximum number for digits"""
        result = weekly_behavior.format_number(9999)
        assert result == "W9999"

    def test_formats_zero(self, weekly_behavior) -> None:

        """Formats zero correctly"""
        result = weekly_behavior.format_number(0)
        assert result == "W0000"

    def test_respects_different_digits(self, monthly_behavior) -> None:

        """Respects different digit count"""
        result = monthly_behavior.format_number(42)
        assert result == "M042"

    def test_formats_with_different_prefix(self) -> None:

        """Formats with different prefix"""
        metadata = LevelMetadata(
            name="quarterly",
            prefix="Q",
            digits=4,
            dir="3_Quarterly",
            source="monthly",
            next_level=None,
        )
        behavior = StandardLevelBehavior(metadata)

        result = behavior.format_number(1)
        assert result == "Q0001"


class TestStandardLevelBehaviorShouldCascade:
    """StandardLevelBehavior.should_cascade() tests"""

    def test_returns_true_when_next_level_exists(self) -> None:

        """Returns True when next_level is defined"""
        metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )
        behavior = StandardLevelBehavior(metadata)

        assert behavior.should_cascade() is True

    def test_returns_false_when_no_next_level(self) -> None:

        """Returns False when next_level is None"""
        metadata = LevelMetadata(
            name="centurial",
            prefix="C",
            digits=4,
            dir="8_Centurial",
            source="multi_decadal",
            next_level=None,
        )
        behavior = StandardLevelBehavior(metadata)

        assert behavior.should_cascade() is False


# =============================================================================
# LoopLevelBehavior Tests
# =============================================================================


class TestLoopLevelBehaviorInit:
    """LoopLevelBehavior initialization tests"""

    def test_init_no_args(self) -> None:

        """Initializes without arguments"""
        behavior = LoopLevelBehavior()
        assert behavior is not None


class TestLoopLevelBehaviorFormatNumber:
    """LoopLevelBehavior.format_number() tests"""

    @pytest.fixture
    def loop_behavior(self):

        """Loop level behavior"""
        return LoopLevelBehavior()

    def test_formats_with_l_prefix(self, loop_behavior) -> None:

        """Formats with L prefix"""
        result = loop_behavior.format_number(1)
        assert result == "L00001"

    def test_formats_larger_number(self, loop_behavior) -> None:

        """Formats larger numbers with 5 digits"""
        result = loop_behavior.format_number(12345)
        assert result == "L12345"

    def test_formats_zero(self, loop_behavior) -> None:

        """Formats zero correctly"""
        result = loop_behavior.format_number(0)
        assert result == "L00000"

    def test_uses_5_digit_padding(self, loop_behavior) -> None:

        """Uses 5-digit zero padding"""
        result = loop_behavior.format_number(42)
        assert result == "L00042"
        assert len(result) == 6  # L + 5 digits


class TestLoopLevelBehaviorShouldCascade:
    """LoopLevelBehavior.should_cascade() tests"""

    def test_always_returns_false(self) -> None:

        """Loop level never cascades"""
        behavior = LoopLevelBehavior()
        assert behavior.should_cascade() is False


# =============================================================================
# Strategy Pattern Integration Tests
# =============================================================================


class TestStrategyPatternIntegration:
    """Strategy pattern integration tests"""

    def test_polymorphic_format_number(self) -> None:

        """Different behaviors produce different formats"""
        weekly_metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        behaviors = [StandardLevelBehavior(weekly_metadata), LoopLevelBehavior()]

        results = [b.format_number(42) for b in behaviors]

        assert results[0] == "W0042"
        assert results[1] == "L00042"

    def test_polymorphic_should_cascade(self) -> None:

        """Different behaviors have different cascade rules"""
        weekly_metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        behaviors = [StandardLevelBehavior(weekly_metadata), LoopLevelBehavior()]

        cascade_results = [b.should_cascade() for b in behaviors]

        assert cascade_results[0] is True  # Weekly cascades to monthly
        assert cascade_results[1] is False  # Loop never cascades

    def test_behavior_substitutability(self):

        """Behaviors are substitutable (Liskov Substitution Principle)"""

        def process_with_behavior(behavior: LevelBehavior) -> str:
            """Function that works with any LevelBehavior"""
            formatted = behavior.format_number(1)
            should_cascade = behavior.should_cascade()
            return f"{formatted}:{should_cascade}"

        weekly_metadata = LevelMetadata(
            name="weekly",
            prefix="W",
            digits=4,
            dir="1_Weekly",
            source="loops",
            next_level="monthly",
        )

        # Both behaviors work with the same function
        result1 = process_with_behavior(StandardLevelBehavior(weekly_metadata))
        result2 = process_with_behavior(LoopLevelBehavior())

        assert result1 == "W0001:True"
        assert result2 == "L00001:False"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
