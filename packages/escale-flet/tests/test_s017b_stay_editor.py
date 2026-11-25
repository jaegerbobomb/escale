"""S017b — Stay editor."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import LONDON_TRIP
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, button, texts, walk

scenarios("S017b.feature")

HOTEL: dict[str, Any] = LONDON_TRIP[1]
CHECK_IN = datetime.fromisoformat(HOTEL["checkinTime"])


def tagged(shell: Shell, key: str, value: str) -> Any:
    [found] = [c for c in walk(shell.body) if isinstance(c.data, dict) and c.data.get(key) == value]
    return found


def run(handler: Any) -> None:
    outcome = handler(None)
    if asyncio.iscoroutine(outcome):
        asyncio.run(outcome)


@dataclass
class World:
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    store: InMemoryReservationStore = field(default_factory=InMemoryReservationStore)
    shell: Shell | None = None

    def open_detail(self) -> Shell:
        r = reservation_from_jsonld(HOTEL, ("d",))
        assert r is not None
        asyncio.run(self.store.add(Document("d", "b.pdf", "application/pdf"), [r]))
        self.shell = Shell(store=self.store, clock=lambda: CHECK_IN - timedelta(hours=3))
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        run(tagged(self.shell, "segment", "ESC-H1").on_click)
        return self.shell

    def open_editor(self) -> Shell:
        shell = self.open_detail()
        run(button(shell.body, "Edit").on_click)
        return shell

    def type_in(self, name: str, value: str) -> None:
        assert self.shell is not None
        text_field = tagged(self.shell, "field", name)
        text_field.value = value
        run(text_field.on_change)


@pytest.fixture
def world() -> World:
    return World()


@given("the detail of a stay with check-out at 11:00")
def detail(world: World) -> None:
    world.open_detail()


@given("the editor of a stay with check-in on 8 July")
@given("the editor of a stay")
def editor(world: World) -> None:
    world.open_editor()


@when("the user edits the check-out to 12:00 and saves")
def edit_check_out(world: World) -> None:
    assert world.shell is not None
    run(button(world.shell.body, "Edit").on_click)
    world.type_in("check_out_time", "12:00")
    run(button(world.shell.body, "Save").on_click)


@when("the user sets the check-out to 7 July")
def check_out_before(world: World) -> None:
    world.type_in("check_out_date", "2026-07-07")


@when("the user empties the name")
def empty_name(world: World) -> None:
    world.type_in("name", "")


@then("the detail shows check-out at 12:00")
def shows_new_check_out(world: World) -> None:
    assert world.shell is not None
    assert texts(tagged(world.shell, "moment", "Check-out"))[1] == "12:00"
    [kept] = asyncio.run(world.store.reservations())
    assert kept.raw["checkoutTime"] == "2026-07-10T12:00:00+01:00"


@then('"Save" is disabled')
def save_disabled(world: World) -> None:
    assert world.shell is not None
    assert button(world.shell.body, "Save").disabled


@then("the editor says the check-out must be after the check-in")
def says_why(world: World) -> None:
    assert world.shell is not None
    assert "The check-out must be after the check-in." in texts(world.shell.body)


# --- details ---


def test_cancel_returns_to_the_detail_unchanged(world: World) -> None:
    shell = world.open_editor()
    world.type_in("name", "Another hotel")
    run(button(shell.body, "Cancel").on_click)
    assert "The Hoxton, Holborn" in texts(shell.body)
    assert not [c for c in walk(shell.body) if isinstance(c.data, dict) and "field" in c.data]


def test_saved_stay_stays_open_and_in_the_trip(world: World) -> None:
    shell = world.open_editor()
    world.type_in("name", "The Hoxton")
    run(button(shell.body, "Save").on_click)
    assert "The Hoxton" in texts(shell.body)
    assert shell.trip is not None and shell.detail in shell.trip.reservations
