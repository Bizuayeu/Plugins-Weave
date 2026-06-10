from __future__ import annotations

import pytest

from domain.exceptions import LeaseConflictError
from domain.lease import SessionLease
from usecases.acquire_lease import AcquireLease

from tests.conftest import t_utc as _t
from tests.usecases.fakes import FakeLeaseStore


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


# === 新規取得の TOCTOU 防御（atomic create 経由） ===


def test_acquire_new_lease_goes_through_atomic_create():
    """新規取得は save でなく try_create（排他作成）を通る。

    load→check→save の窓で並走 2 プロセスが両方「不在」を見て両方勝つ
    TOCTOU を、「最初の 1 プロセスだけが OS の排他作成で勝つ」に置き換える。
    """
    store = FakeLeaseStore(initial=None)
    uc = AcquireLease(store)
    lease = uc.execute(owner="me", now=_t(0), ttl_seconds=120)
    assert lease.owner == "me"
    assert store.try_create_calls == 1
    assert store.lease == lease


def test_acquire_conflicts_when_create_race_lost_to_fresh_owner():
    """try_create 負け→再 load で fresh な並走者が見えたら conflict（後着は負け）。"""
    store = FakeLeaseStore(initial=None)
    store.create_race_winner = SessionLease(
        owner="rival", heartbeat=_t(0), ttl_seconds=120
    )
    uc = AcquireLease(store)
    with pytest.raises(LeaseConflictError):
        uc.execute(owner="me", now=_t(1), ttl_seconds=120)
    # 勝者の lease は上書きされない
    assert store.lease.owner == "rival"


def test_acquire_steals_when_create_race_winner_already_stale():
    """try_create 負けでも並走者が既に stale なら奪取（crash 自己治癒と同型）。"""
    store = FakeLeaseStore(initial=None)
    store.create_race_winner = SessionLease(
        owner="rival", heartbeat=_t(0), ttl_seconds=60
    )
    uc = AcquireLease(store)
    # 200秒後 = rival は stale
    lease = uc.execute(owner="me", now=_t(200), ttl_seconds=120)
    assert lease.owner == "me"
    assert store.lease.owner == "me"
