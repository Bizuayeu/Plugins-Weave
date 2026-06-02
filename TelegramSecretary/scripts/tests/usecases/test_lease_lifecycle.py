from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from domain.exceptions import LeaseConflictError
from domain.lease import SessionLease
from usecases.release_lease import ReleaseLease
from usecases.renew_lease import RenewLease

from tests.usecases.fakes import FakeLeaseStore


def _t(seconds: int = 0) -> datetime:
    base = datetime(2026, 5, 26, 12, 0, 0, tzinfo=timezone.utc)
    return base + timedelta(seconds=seconds)


def test_renew_updates_heartbeat_when_owner_matches():
    existing = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    store = FakeLeaseStore(initial=existing)
    uc = RenewLease(store)
    renewed = uc.execute(owner="me", now=_t(60))
    assert renewed.heartbeat == _t(60)
    assert store.lease.heartbeat == _t(60)


def test_renew_fails_when_no_lease():
    store = FakeLeaseStore(initial=None)
    uc = RenewLease(store)
    with pytest.raises(LeaseConflictError):
        uc.execute(owner="me", now=_t(0))


def test_renew_fails_when_owner_mismatches():
    existing = SessionLease(owner="other", heartbeat=_t(0), ttl_seconds=120)
    store = FakeLeaseStore(initial=existing)
    uc = RenewLease(store)
    with pytest.raises(LeaseConflictError):
        uc.execute(owner="me", now=_t(60))
    # 他人のリースを書き換えない
    assert store.lease == existing


def test_release_clears_own_lease():
    existing = SessionLease(owner="me", heartbeat=_t(0), ttl_seconds=120)
    store = FakeLeaseStore(initial=existing)
    uc = ReleaseLease(store)
    uc.execute(owner="me")
    assert store.lease is None
    assert store.clear_calls == 1


def test_release_is_noop_when_no_lease():
    store = FakeLeaseStore(initial=None)
    uc = ReleaseLease(store)
    uc.execute(owner="me")
    assert store.clear_calls == 0


def test_release_does_not_clear_others_lease():
    existing = SessionLease(owner="other", heartbeat=_t(0), ttl_seconds=120)
    store = FakeLeaseStore(initial=existing)
    uc = ReleaseLease(store)
    uc.execute(owner="me")
    # 他人のリースは触らない（誤解放防止）
    assert store.lease == existing
    assert store.clear_calls == 0
