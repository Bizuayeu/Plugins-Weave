from __future__ import annotations

from domain.authorization import AuthorizedChats


def test_is_authorized_allows_listed_chat():
    chats = AuthorizedChats.from_iterable([100, 200])
    assert chats.is_authorized(100) is True
    assert chats.is_authorized(200) is True


def test_is_authorized_rejects_unlisted_chat():
    chats = AuthorizedChats.from_iterable([100])
    assert chats.is_authorized(999) is False


def test_empty_allowlist_rejects_all():
    chats = AuthorizedChats.from_iterable([])
    assert chats.is_authorized(0) is False
    assert chats.is_authorized(1) is False


def test_frozen_after_construction():
    chats = AuthorizedChats.from_iterable([100])
    # frozenset なので変更不可、dataclass(frozen=True) で属性も再代入不可
    import pytest
    with pytest.raises(AttributeError):
        chats.chat_ids = frozenset([200])  # type: ignore[misc]
