"""S018 — Add a stay by hand: "Add → Add manually…", then "Stay"."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.importer import Importer
from escale_core.store import InMemoryReservationStore
from escale_flet.shell import Shell, Tab
from escale_flet.testing import FakePage, button, click, tagged, texts

scenarios("S018.feature")

DATA = Path(__file__).parents[2] / "escale-core" / "tests" / "data"
NOW = datetime.fromisoformat("2027-06-01T09:00:00+02:00")


@pytest.fixture(autouse=True)
def paris(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TZ", "Europe/Paris")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


class World:
    def __init__(self, width: int = 1000) -> None:
        self.page = FakePage(width=width)
        self.store = InMemoryReservationStore()
        no_file = DATA / "no-reservation.pdf"

        async def choose_file() -> Path | None:
            return no_file

        self.shell = Shell(
            importer=Importer(FakeExtractor([]), self.store),
            store=self.store,
            choose_file=choose_file,
            clock=lambda: NOW,
        )
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())

    def menu_entry(self, label: str) -> Any:
        [menu] = [c for c in self.shell.add_button.controls if isinstance(c, ft.PopupMenuButton)]
        [item] = [i for i in menu.items if cast(ft.Text, i.content).value == label]
        return item

    def choose(self, kind: str) -> None:
        click(tagged(self.page.dialog, "manual_kind", kind))

    def type_in(self, name: str, value: str) -> None:
        field = tagged(self.page.dialog, "field", name)
        field.value = value
        field.on_change(None)


@pytest.fixture
def world() -> World:
    return World()


@given("an empty trip list")
def empty(world: World) -> None:
    assert asyncio.run(world.store.reservations()) == ()


@given("the empty editor of a new stay")
def new_editor(world: World) -> None:
    click(world.menu_entry("Add manually…"))
    world.choose("stay")


@given("a file with no reservation was imported")
def failed_import(world: World) -> None:
    asyncio.run(world.shell.start_import())
    assert "Nothing recognised" in texts(world.page.dialog)


@when('the user adds a stay "Hôtel du Nord", Paris, from 8 July 15:00 to 10 July 11:00')
def add_stay(world: World) -> None:
    new_editor(world)
    for name, value in (
        ("name", "Hôtel du Nord"),
        ("city", "Paris"),
        ("check_in_date", "2027-07-08"),
        ("check_in_time", "15:00"),
        ("check_out_date", "2027-07-10"),
        ("check_out_time", "11:00"),
    ):
        world.type_in(name, value)
    click(button(world.page.dialog, "Save"))


@when("the user fills the name and cancels")
def fill_and_cancel(world: World) -> None:
    world.type_in("name", "Hôtel du Nord")
    click(button(world.page.dialog, "Cancel"))


@when('the user chooses "Add manually" then "Stay"')
def manual_after_import(world: World) -> None:
    click(button(world.page.dialog, "Add manually"))
    world.choose("stay")


@then("the stay is saved")
def saved(world: World) -> None:
    [stay] = asyncio.run(world.store.reservations())
    assert stay.type == "LodgingReservation"
    assert stay.raw["checkinTime"] == "2027-07-08T15:00:00+02:00"
    assert world.page.dialog is None


@then("a trip to Paris shows it")
def trip_shows_it(world: World) -> None:
    shell = world.shell
    shown = shell._shown()
    assert shell.selected == Tab.CURRENT  # the next trip to start
    assert shown is not None and shown.name == "Paris"
    assert shell.detail is not None and shell.detail in shown.reservations
    assert "Hôtel du Nord" in texts(shell.body)


@then("no stay is saved")
def nothing_saved(world: World) -> None:
    assert asyncio.run(world.store.reservations()) == ()
    assert world.page.dialog is None


@then("the editor of a new stay is shown")
def editor_shown(world: World) -> None:
    assert len(world.page.dialogs) == 1
    assert "New Stay" in texts(world.page.dialog)
    assert tagged(world.page.dialog, "field", "name").value == ""


# --- details ---


def test_the_chooser_offers_the_kinds_and_only_stay_for_now(world: World) -> None:
    click(world.menu_entry("Add manually…"))
    rows = [
        (c.data["manual_kind"], bool(c.disabled))
        for c in _walk(world.page.dialog)
        if isinstance(c.data, dict) and "manual_kind" in c.data
    ]
    assert rows == [
        ("stay", False),
        ("flight", True),
        ("train", True),
        ("bus", True),
        ("ferry", True),
        ("event", True),
        ("restaurant", True),
    ]
    assert "Add Manually" in texts(world.page.dialog)


def test_cancelling_the_chooser_adds_nothing(world: World) -> None:
    click(world.menu_entry("Add manually…"))
    click(button(world.page.dialog, "Cancel"))
    assert world.page.dialog is None


def test_on_a_phone_the_chooser_and_the_editor_are_bottom_sheets() -> None:
    world = World(width=380)
    click(cast(Any, world.shell.add_menu_compact.items)[-1])
    assert isinstance(world.page.dialog, ft.BottomSheet)
    world.choose("stay")
    assert isinstance(world.page.dialog, ft.BottomSheet) and len(world.page.dialogs) == 1


def test_a_new_stay_survives_a_resize_of_its_editor(world: World) -> None:
    new_editor(world)
    world.type_in("name", "Hôtel du Nord")
    world.shell.resize(380)
    assert "New Stay" in texts(world.page.dialog)
    assert tagged(world.page.dialog, "field", "name").value == "Hôtel du Nord"


def test_editing_an_open_detail_after_cancelling_a_new_stay_edits_the_detail(
    world: World,
) -> None:
    add_stay(world)
    stay = world.shell.detail
    new_editor(world)
    click(button(world.page.dialog, "Cancel"))
    world.shell.edit()
    assert "Edit Stay" in texts(world.page.dialog)
    assert tagged(world.page.dialog, "field", "name").value == "Hôtel du Nord"
    assert world.shell.detail is stay


def test_a_past_stay_opens_its_trip_in_my_trips(world: World) -> None:
    new_editor(world)
    for name, value in (
        ("name", "Hôtel du Nord"),
        ("city", "Paris"),
        ("check_in_date", "2026-07-08"),
        ("check_in_time", "15:00"),
        ("check_out_date", "2026-07-10"),
        ("check_out_time", "11:00"),
    ):
        world.type_in(name, value)
    click(button(world.page.dialog, "Save"))
    shell = world.shell
    assert shell.selected == Tab.TRIPS
    assert shell.browsed is not None and shell.browsed.name == "Paris"
    assert shell.detail is not None and shell.detail in shell.browsed.reservations


def _walk(control: Any) -> list[Any]:
    from escale_flet.testing import walk

    return list(walk(control))


def test_the_chooser_becomes_a_bottom_sheet_when_the_window_narrows(world: World) -> None:
    click(world.menu_entry("Add manually…"))
    assert isinstance(world.page.dialog, ft.AlertDialog)
    world.shell.resize(380)
    assert len(world.page.dialogs) == 1 and isinstance(world.page.dialog, ft.BottomSheet)
    world.choose("stay")
    assert "New Stay" in texts(world.page.dialog)
