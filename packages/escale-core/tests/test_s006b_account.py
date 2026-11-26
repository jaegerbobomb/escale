"""S006b — the Nextcloud account in the preferences: the core part."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from escale_core.account import Account
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.nextcloud import Problem
from escale_core.passwords import MemoryPasswords
from escale_core.settings import AccountSettings, SettingsFile, default_config_dir

URL, LOGIN, PASSWORD = "cloud.example.org", "jane", "app-pw-1"
KEY = "jane@https://cloud.example.org/remote.php/dav"


@pytest.fixture
def settings(tmp_path: Path) -> SettingsFile:
    return SettingsFile(tmp_path / "escale" / "settings.json")


def account(
    settings: SettingsFile, server: FakeNextcloud, passwords: MemoryPasswords | None = None
) -> tuple[Account, MemoryPasswords]:
    kept = passwords or MemoryPasswords(lasting=True)
    return Account(settings, kept, lambda url, login, pw: server), kept


def test_connecting_saves_the_account_and_puts_the_password_in_the_keyring(
    settings: SettingsFile,
) -> None:
    a, passwords = account(settings, FakeNextcloud(calendars=["Personal"]))
    assert asyncio.run(a.connect(f" {URL} ", "jane ", PASSWORD))
    assert a.connected and a.remembered
    assert [c.name for c in a.calendars] == ["Personal"]
    assert settings.account() == AccountSettings(URL, LOGIN)
    assert passwords.saved == {KEY: PASSWORD}
    assert PASSWORD not in settings.path.read_text()


def test_a_refused_password_saves_nothing(settings: SettingsFile) -> None:
    a, passwords = account(settings, FakeNextcloud(password_ok=False))
    assert not asyncio.run(a.connect(URL, LOGIN, "wrong"))
    assert a.problem is Problem.REFUSED and not a.connected
    assert not settings.path.exists() and passwords.saved == {}


def test_without_a_keyring_the_password_is_not_remembered(settings: SettingsFile) -> None:
    a, _ = account(settings, FakeNextcloud(), MemoryPasswords(lasting=False))
    asyncio.run(a.connect(URL, LOGIN, PASSWORD))
    assert a.connected and not a.remembered


def test_the_account_is_restored_when_its_password_is_in_the_keyring(
    settings: SettingsFile,
) -> None:
    first, passwords = account(settings, FakeNextcloud(calendars=["Work"]))
    asyncio.run(first.connect(URL, LOGIN, PASSWORD))
    again, _ = account(settings, FakeNextcloud(calendars=["Work"]), passwords)
    asyncio.run(again.restore())
    assert again.connected and again.saved.login == LOGIN and again.host == URL
    asyncio.run(again.load_calendars())
    assert [c.name for c in again.calendars] == ["Work"]


def test_without_its_password_the_account_is_not_restored(settings: SettingsFile) -> None:
    settings.save_account(AccountSettings(URL, LOGIN))
    a, _ = account(settings, FakeNextcloud())
    asyncio.run(a.restore())
    assert not a.connected


def test_choosing_a_calendar_saves_it(settings: SettingsFile) -> None:
    a, _ = account(settings, FakeNextcloud(calendars=["Personal", "Work"]))
    asyncio.run(a.connect(URL, LOGIN, PASSWORD))
    asyncio.run(a.choose(a.calendars[1]))
    assert settings.account().calendar == a.calendars[1].url


def test_creating_trips_chooses_it_and_is_offered_once(settings: SettingsFile) -> None:
    a, _ = account(settings, FakeNextcloud(calendars=["Personal"]))
    asyncio.run(a.connect(URL, LOGIN, PASSWORD))
    assert a.can_create_trips
    asyncio.run(a.create_trips())
    assert [c.name for c in a.calendars] == ["Personal", "Trips"]
    assert settings.account().calendar == a.calendars[1].url
    assert not a.can_create_trips


def test_disconnecting_forgets_the_password_and_the_account(settings: SettingsFile) -> None:
    a, passwords = account(settings, FakeNextcloud())
    asyncio.run(a.connect(URL, LOGIN, PASSWORD))
    asyncio.run(a.disconnect())
    assert not a.connected and passwords.saved == {}
    assert settings.account() == AccountSettings()


def test_saving_the_account_keeps_the_other_settings(settings: SettingsFile) -> None:
    settings.path.parent.mkdir(parents=True)
    settings.path.write_text(json.dumps({"theme": "dark"}))
    settings.save_account(AccountSettings(URL, LOGIN))
    settings.save_account(None)
    assert json.loads(settings.path.read_text()) == {"theme": "dark"}


def test_an_unreadable_settings_file_is_an_empty_one(settings: SettingsFile) -> None:
    settings.path.parent.mkdir(parents=True)
    settings.path.write_text("{not json")
    assert settings.account() == AccountSettings()


def test_the_settings_follow_xdg(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert default_config_dir() == tmp_path / "escale"
