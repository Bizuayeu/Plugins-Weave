from __future__ import annotations

from domain.rate_limit import RateLimit
from tests.conftest import t_utc as _t


def test_events_within_limit_are_admitted_and_accumulated():
    limit = RateLimit(window_seconds=60, max_events=2)
    admitted, history = limit.admit([], _t(0))
    assert admitted is True
    assert history == [_t(0)]

    admitted, history = limit.admit(history, _t(1))
    assert admitted is True
    assert history == [_t(0), _t(1)]


def test_event_beyond_max_is_rejected_and_not_recorded():
    limit = RateLimit(window_seconds=60, max_events=2)
    history = [_t(0), _t(1)]
    admitted, new_history = limit.admit(history, _t(2))
    assert admitted is False
    # 拒否したイベントは履歴に積まない（窓が開くのを遅らせない）
    assert new_history == history


def test_events_older_than_window_are_pruned():
    limit = RateLimit(window_seconds=60, max_events=2)
    history = [_t(0), _t(1)]
    admitted, new_history = limit.admit(history, _t(60))
    assert admitted is True
    # _t(0) はちょうど窓外、_t(1) はまだ窓内
    assert new_history == [_t(1), _t(60)]


def test_event_exactly_window_seconds_old_is_outside_the_window():
    # 境界作法は WatchWindow.is_expired と同一（ちょうどは窓外）
    limit = RateLimit(window_seconds=60, max_events=1)
    admitted, history = limit.admit([_t(0)], _t(60))
    assert admitted is True
    assert history == [_t(60)]


def test_non_positive_max_events_disables_the_limit():
    limit = RateLimit(window_seconds=60, max_events=0)
    history = [_t(0)] * 100
    admitted, new_history = limit.admit(history, _t(1))
    assert admitted is True
    # 無制限時は履歴を伸ばさない（無為なメモリ増を避ける）
    assert new_history == history


def test_defaults_are_safe_side_and_generous_for_humans():
    limit = RateLimit()
    assert limit.window_seconds > 0
    assert limit.max_events > 0
