from __future__ import annotations

from datetime import datetime, timedelta, timezone

from domain.lease import SessionLease, utc_now

from tests.conftest import t_utc as _t


def test_fresh_lease_is_not_stale():
    lease = SessionLease(owner="session-A", heartbeat=_t(0), ttl_seconds=120)
    assert lease.is_stale(_t(60)) is False


def test_lease_becomes_stale_after_ttl():
    lease = SessionLease(owner="session-A", heartbeat=_t(0), ttl_seconds=120)
    # ちょうど境界では stale ではない、超えたら stale
    assert lease.is_stale(_t(120)) is False
    assert lease.is_stale(_t(121)) is True


def test_held_by_other_when_different_owner_and_fresh():
    lease = SessionLease(owner="session-A", heartbeat=_t(0), ttl_seconds=120)
    assert lease.held_by_other(now=_t(30), me="session-B") is True


def test_not_held_by_other_when_stale():
    lease = SessionLease(owner="session-A", heartbeat=_t(0), ttl_seconds=120)
    # stale ならば自分が奪取できるので held_by_other は False
    assert lease.held_by_other(now=_t(200), me="session-B") is False


def test_not_held_by_other_when_same_owner():
    lease = SessionLease(owner="session-A", heartbeat=_t(0), ttl_seconds=120)
    assert lease.held_by_other(now=_t(30), me="session-A") is False


def test_renew_updates_heartbeat_only():
    lease = SessionLease(owner="session-A", heartbeat=_t(0), ttl_seconds=120)
    renewed = lease.renew(_t(60))
    assert renewed.heartbeat == _t(60)
    assert renewed.owner == "session-A"
    assert renewed.ttl_seconds == 120


def test_utc_now_is_timezone_aware():
    now = utc_now()
    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)
