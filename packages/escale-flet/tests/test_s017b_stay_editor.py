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
from escale_flet.testing import FakePage, button, texts
from escale_flet.testing import tagged as find

scenarios("S017b.feature")

HOTEL: dict[str, Any] = LONDON_TRIP[1]
CHECK_IN = datetime.fromisoformat(HOTEL["checkinTime"])


def tagged(shell: Shell, key: str, value: str) -> Any:
    return find(shell.body, key, value)


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
        assert self.page.appbar is not None
        run(find(self.page.appbar.actions, "edit", True).on_click)
        return shell

    def type_in(self, name: str, value: str) -> None:
        text_field = find(self.page.dialog, "field", name)
        text_field.value = value
        run(text_field.on_change)


@pytest.fixture
def world() -> World:
    return World()


@given("the detail of a stay with check-out at 11:00")
def detail(world: World) -> None:
    pass  # opened by the "when" step, through the header bar's Edit


@given("the editor of a stay with check-in on 8 July")
@given("the editor of a stay")
def editor(world: World) -> None:
    world.open_editor()


@when("the user edits the check-out to 12:00 and saves")
def edit_check_out(world: World) -> None:
    world.open_editor()
    world.type_in("check_out_time", "12:00")
    run(button(world.page.dialog, "Save").on_click)


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
    assert button(world.page.dialog, "Save").disabled


@then("the editor says the check-out must be after the check-in")
def says_why(world: World) -> None:
    assert "The check-out must be after the check-in." in texts(world.page.dialog)


# --- details ---


def test_cancel_returns_to_the_detail_unchanged(world: World) -> None:
    shell = world.open_editor()
    world.type_in("name", "Another hotel")
    run(button(world.page.dialog, "Cancel").on_click)
    assert world.page.dialog is None
    assert "The Hoxton, Holborn" in texts(shell.body)


def test_saved_stay_stays_open_and_in_the_trip(world: World) -> None:
    shell = world.open_editor()
    world.type_in("name", "The Hoxton")
    run(button(world.page.dialog, "Save").on_click)
    assert world.page.dialog is None
    assert "The Hoxton" in texts(shell.body)
    assert shell.trip is not None and shell.detail in shell.trip.reservations


def test_the_check_out_date_can_be_picked(world: World) -> None:
    world.open_editor()
    editor = world.page.dialog
    run(find(editor, "picker", "check_out_date").on_click)
    picker = world.page.dialog
    assert isinstance(picker, ft.DatePicker)
    picker.value = datetime(2026, 7, 7)
    run(picker.on_change)
    assert find(editor, "field", "check_out_date").value == "2026-07-07"
    assert "The check-out must be after the check-in." in texts(editor)
