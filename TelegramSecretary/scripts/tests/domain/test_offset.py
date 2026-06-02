from __future__ import annotations

import pytest

from domain.exceptions import InvalidOffsetError
from domain.offset import UpdateOffset


def test_initial_offset_is_zero():
    assert UpdateOffset.initial().value == 0


def test_negative_offset_raises():
    with pytest.raises(InvalidOffsetError):
        UpdateOffset(value=-1)


def test_advance_with_larger_id_increments():
    offset = UpdateOffset(value=10)
    advanced = offset.advance(update_id=15)
    assert advanced.value == 16  # max(10, 15+1) = 16


def test_advance_with_smaller_id_does_not_rewind():
    # 古い update を再処理しても巻き戻らない（冪等）
    offset = UpdateOffset(value=20)
    advanced = offset.advance(update_id=5)
    assert advanced.value == 20  # max(20, 5+1) = 20


def test_advance_with_equal_id_increments_by_one():
    offset = UpdateOffset(value=10)
    advanced = offset.advance(update_id=9)
    assert advanced.value == 10  # max(10, 9+1) = 10
    advanced2 = offset.advance(update_id=10)
    assert advanced2.value == 11  # max(10, 10+1) = 11


def test_offset_is_immutable():
    offset = UpdateOffset(value=10)
    with pytest.raises(AttributeError):
        offset.value = 20  # type: ignore[misc]
