from __future__ import annotations

import pytest

from domain.session_config import MAX_SECONDS, MIN_SECONDS, SessionDuration


def test_typical_duration_is_valid():
    """旧既定 2h（7200秒）が有効値であること。"""
    assert SessionDuration.from_seconds(7200).seconds == 7200


def test_upper_boundary_is_inclusive():
    """上限ちょうど（24h=86400秒）は許容（watch_window の「ちょうど境界」作法）。"""
    assert SessionDuration.from_seconds(MAX_SECONDS).seconds == 86400


def test_above_upper_boundary_raises():
    """上限超過（86401秒）は ValueError。"""
    with pytest.raises(ValueError):
        SessionDuration.from_seconds(MAX_SECONDS + 1)


def test_lower_boundary_is_inclusive():
    """下限ちょうど（1秒）は許容。"""
    assert SessionDuration.from_seconds(MIN_SECONDS).seconds == 1


def test_zero_raises():
    """0 は不正。watch_window の <=0=無限窓 とは別物——session 総枠で 0 は不正。"""
    with pytest.raises(ValueError):
        SessionDuration.from_seconds(0)


def test_negative_raises():
    """負値は不正。"""
    with pytest.raises(ValueError):
        SessionDuration.from_seconds(-1)


def test_short_duration_for_testing_is_valid():
    """テスト/観測用の短 duration（60秒）が通ること（SciEngLoop の観測装置）。"""
    assert SessionDuration.from_seconds(60).seconds == 60
