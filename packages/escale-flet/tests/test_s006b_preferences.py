"""S006b — Nextcloud account in the preferences."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.account import Account
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.nextcloud import Problem
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import LONDON_TRIP
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, button, click, tagged, texts, walk

scenarios("S006b.feature")


@dataclass
class World:
    settings: SettingsFile
    server: FakeNextcloud = field(default_factory=lambda: FakeNextcloud(["Personal", "Work"]))
    passwords: MemoryPasswords = field(default_factory=lambda: MemoryPasswords(lasting=True))
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    shell: Shell | None = None

    def account(self) -> Account:
        return Account(self.settings, self.passwords, lambda url, login, pw: self.server)

    def open_preferences(self, account: Account | None = None) -> Any:
        self.shell = Shell(account=account or self.account())
        self.shell.mount(cast(ft.Page, self.page))
        assert self.page.appbar is not None
        menu = tagged(self.page.appbar.actions, "primary_menu")
        [preferences] = [i for i in menu.items if i.content.value == "Preferences"]
        click(preferences)
        return self.page.dialog

    def type_in(self, name: str, value: str) -> None:
        entry = tagged(self.page.dialog, "field", name)
        entry.value = value
        entry.on_change(None)

    def connect(self, password: str) -> None:
        self.type_in("url", "cloud.example.org")
        self.type_in("login", "jane")
        self.type_in("password", password)
        click(button(self.page.dialog, "Connect"))


def calendars(dialog: Any) -> list[str]:
    return [c.label for c in walk(tagged(dialog, "calendars")) if isinstance(c, ft.Radio)]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(SettingsFile(tmp_path / "settings.json"))


@given("a reachable Nextcloud server")
def reachable(world: World) -> None:
    world.open_preferences()


@when("the user enters its URL, a login and a valid app password")
def valid(world: World) -> None:
    world.connect("app-pw")


@when("the user enters a wrong app password")
def wrong(world: World) -> None:
    world.server.password_ok = False
    world.connect("wrong")


@then("the user's calendars are listed")
def listed(world: World) -> None:
    assert calendars(world.page.dialog) == ["Personal", "Work"]


@then("the account is shown as connected")
def shown_connected(world: World) -> None:
    assert "Connected as jane" in texts(world.page.dialog)


@then("the app says the credentials were refused")
def refused(world: World) -> None:
    assert Problem.REFUSED.value in texts(world.page.dialog)


@then("nothing is saved")
def nothing_saved(world: World) -> None:
    assert not world.settings.path.exists() and world.passwords.saved == {}


# --- details ---


def test_connect_waits_for_the_three_fields(world: World) -> None:
    world.open_preferences()
    assert button(world.page.dialog, "Connect").disabled
    world.type_in("url", "cloud.example.org")
    world.type_in("login", "jane")
    assert button(world.page.dialog, "Connect").disabled
    world.type_in("password", "x")
    assert not button(world.page.dialog, "Connect").disabled


def test_the_password_field_hides_what_is_typed(world: World) -> None:
    world.open_preferences()
    assert tagged(world.page.dialog, "field", "password").password


def test_choosing_a_calendar_saves_it(world: World) -> None:
    world.open_preferences()
    world.connect("app-pw")
    group = tagged(world.page.dialog, "calendars")
    work = "https://cloud.test/remote.php/dav/calendars/u/work/"
    group.value = work
    asyncio.run(group.on_change(None))
    assert world.settings.account().calendar == work


def test_create_a_trips_calendar(world: World) -> None:
    world.open_preferences()
    world.connect("app-pw")
    click(tagged(world.page.dialog, "action", "Create a Trips calendar"))
    assert calendars(world.page.dialog) == ["Personal", "Work", "Trips"]
    assert world.settings.account().calendar.endswith("/trips/")
    with pytest.raises(LookupError):
        tagged(world.page.dialog, "action", "Create a Trips calendar")


def test_disconnect_forgets_the_account(world: World) -> None:
    world.open_preferences()
    world.connect("app-pw")
    click(tagged(world.page.dialog, "action", "Disconnect"))
    assert world.passwords.saved == {}
    assert button(world.page.dialog, "Connect").disabled  # the empty form again


def test_a_saved_account_opens_as_connected(world: World) -> None:
    first = world.account()
    asyncio.run(first.connect("cloud.example.org", "jane", "app-pw"))
    again = world.account()
    asyncio.run(again.restore())
    world.open_preferences(again)
    assert "Connected as jane" in texts(world.page.dialog)
    assert calendars(world.page.dialog) == ["Personal", "Work"]


def test_without_a_keyring_the_user_is_told(world: World) -> None:
    world.passwords = MemoryPasswords(lasting=False)
    world.open_preferences()
    world.connect("app-pw")
    assert any("asked again" in t for t in texts(world.page.dialog))


def test_close_button_closes_the_preferences(world: World) -> None:
    world.open_preferences()
    click(tagged(world.page.dialog, "close"))
    assert world.page.dialog is None


def test_on_a_phone_the_preferences_are_a_sheet_and_keep_what_was_typed(world: World) -> None:
    world.open_preferences()
    assert isinstance(world.page.dialog, ft.AlertDialog)
    world.type_in("url", "cloud.example.org")
    world.page.resize(380)
    assert isinstance(world.page.dialog, ft.BottomSheet)
    assert tagged(world.page.dialog, "field", "url").value == "cloud.example.org"


def test_the_primary_menu_is_not_on_a_detail(world: World) -> None:
    hotel = reservation_from_jsonld(LONDON_TRIP[1], ("d",))
    assert hotel is not None
    store = InMemoryReservationStore()
    asyncio.run(store.add(Document("d", "b.pdf", "application/pdf"), [hotel]))
    check_in = datetime.fromisoformat(LONDON_TRIP[1]["checkinTime"])
    shell = Shell(store=store, clock=lambda: check_in, account=world.account())
    shell.mount(cast(ft.Page, world.page))
    asyncio.run(shell.refresh())
    assert world.page.appbar is not None
    tagged(world.page.appbar.actions, "primary_menu")
    assert shell.trip is not None
    shell.open_detail(shell.trip.reservations[0])
    with pytest.raises(LookupError):
        tagged(world.page.appbar.actions, "primary_menu")
