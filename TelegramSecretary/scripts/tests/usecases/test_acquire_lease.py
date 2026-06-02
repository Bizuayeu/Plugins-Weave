from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domain.exceptions import LeaseConflictError
from domain.lease import SessionLease
from usecases.acquire_lease import AcquireLease

from tests.usecases.fakes import FakeLeaseStore


def _t(seconds: int = 0) -> datetime:
    base = datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=seconds)


def test_acquire_when_no_existing_lease():
    store = FakeLeaseStore(initial=None)
    uc = AcquireLease(store)
    lease = uc.execute(owner="me", now=_t(0), ttl_seconds=120)
    assert lease.owner == "me"
    assert lease.heartbeat == _t(0)
    assert store.lease == lease


def test_acquire_steals_stale_lease_of_other_owner():
    existing = SessionLease(owner="zombie", heartbeat=_t(0), ttl_seconds=60)
    store = FakeLeaseStore(initial=existing)
    uc = AcquireLease(store)
    # 200秒経過、stale ＝ 奪取可能
    lease = uc.execute(owner="me", now=_t(200), ttl_seconds=120)
    assert lease.owner == "me"
    assert store.lease.owner == "me"


def test_acquire_refreshes_own_existing_lease():
    existing = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    store = FakeLeaseStore(initial=existing)
    uc = AcquireLease(store)
    lease = uc.execute(owner="me", now=_t(30), ttl_seconds=120)
    assert lease.owner == "me"
    assert lease.heartbeat == _t(30)


def test_acquire_fails_when_other_owner_has_fresh_lease():
    existing = SessionLease(owner="other", heartbeat=_t(0), ttl_seconds=120)
    store = FakeLeaseStore(initial=existing)
    uc = AcquireLease(store)
    with pytest.raises(LeaseConflictError):
        uc.execute(owner="me", now=_t(30), ttl_seconds=120)
    # 既存リースは保護される
    assert store.lease == existing
