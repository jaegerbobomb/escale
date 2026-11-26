"""The system keyring adapter (S006b), with ``keyring``'s calls replaced."""

from __future__ import annotations

import asyncio

import keyring
import pytest
from keyring.errors import NoKeyringError, PasswordDeleteError

from escale_core.adapters.system_keyring import SERVICE, SystemKeyring


def _refuse(*_: object) -> None:
    raise NoKeyringError


def test_a_keyring_keeps_the_password(monkeypatch: pytest.MonkeyPatch) -> None:
    saved: dict[tuple[str, str], str] = {}
    monkeypatch.setattr(keyring, "set_password", lambda s, a, p: saved.update({(s, a): p}))
    monkeypatch.setattr(keyring, "get_password", lambda s, a: saved.get((s, a)))
    store = SystemKeyring()
    assert asyncio.run(store.set("jane@dav", "pw"))
    assert saved == {(SERVICE, "jane@dav"): "pw"}
    assert asyncio.run(SystemKeyring().get("jane@dav")) == "pw"


def test_without_a_keyring_the_password_lasts_until_the_app_quits(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("set_password", "get_password", "delete_password"):
        monkeypatch.setattr(keyring, name, _refuse)
    store = SystemKeyring()
    assert not asyncio.run(store.set("jane@dav", "pw"))
    assert asyncio.run(store.get("jane@dav")) == "pw"
    assert asyncio.run(SystemKeyring().get("jane@dav")) is None
    asyncio.run(store.delete("jane@dav"))
    assert asyncio.run(store.get("jane@dav")) is None


def test_deleting_a_missing_password_is_fine(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(*_: object) -> None:
        raise PasswordDeleteError

    monkeypatch.setattr(keyring, "delete_password", missing)
    asyncio.run(SystemKeyring().delete("jane@dav"))
