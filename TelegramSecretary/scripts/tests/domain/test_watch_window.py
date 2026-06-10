from __future__ import annotations

from domain.watch_window import WatchWindow

from tests.conftest import t_utc as _t


def test_fresh_window_is_not_expired():
    window = WatchWindow(started_at=_t(0), max_duration_seconds=580)
    assert window.is_expired(_t(300)) is False


def test_window_expires_after_max_duration():
    window = WatchWindow(started_at=_t(0), max_duration_seconds=580)
    # ちょうど境界では満了ではない、超えたら満了（SessionLease.is_stale と同一作法）
    assert window.is_expired(_t(580)) is False
    assert window.is_expired(_t(581)) is True


def test_zero_duration_means_infinite_never_expires():
    # 0 = 無限窓（既存 --max-iterations 0=無限 と同型セマンティクス）
    window = WatchWindow(started_at=_t(0), max_duration_seconds=0)
    assert window.is_expired(_t(0)) is False
    assert window.is_expired(_t(100000)) is False


def test_negative_duration_treated_as_infinite():
    # 0 以下はすべて無限扱い（負値を弾かず単に無限とする）
    window = WatchWindow(started_at=_t(0), max_duration_seconds=-1)
    assert window.is_expired(_t(100000)) is False


def test_remaining_seconds_positive_within_window():
    window = WatchWindow(started_at=_t(0), max_duration_seconds=580)
    assert window.remaining_seconds(_t(80)) == 500.0


def test_remaining_seconds_non_positive_after_expiry():
    window = WatchWindow(started_at=_t(0), max_duration_seconds=580)
    # 満了後は 0 以下（クランプせず超過分を負値で返す＝ログ/可観測性用途）
    assert window.remaining_seconds(_t(600)) == -20.0


def test_remaining_seconds_infinite_for_zero_duration():
    window = WatchWindow(started_at=_t(0), max_duration_seconds=0)
    assert window.remaining_seconds(_t(100000)) == float("inf")
