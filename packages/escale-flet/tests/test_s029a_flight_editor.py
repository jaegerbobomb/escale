"""S029a — Edit a flight."""

from __future__ import annotations

import asyncio
import time as pytime
from datetime import UTC, datetime, time, timedelta
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import FLIGHT
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, button, click, tagged, texts, walk

scenarios("S029a.feature")

LEAVES = datetime.fromisoformat(FLIGHT["reservationFor"]["departureTime"])


def picked(picker: ft.DatePicker | ft.TimePicker) -> None:
    """The picker's "OK"."""
    handler: Any = picker.on_change
    handler(None)


class World:
    def __init__(self) -> None:
        self.page = FakePage(width=1000)
        self.store = InMemoryReservationStore()
        r = reservation_from_jsonld(FLIGHT, ("d",))
        assert r is not None
        asyncio.run(self.store.add(Document("d", "b.pdf", "application/pdf"), [r]))
        self.shell = Shell(store=self.store, clock=lambda: LEAVES - timedelta(hours=3))
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        assert self.shell.trip is not None
        self.shell.open_detail(self.shell.trip.reservations[0])

    def open_editor(self) -> None:
        assert self.page.appbar is not None
        click(tagged(self.page.appbar.actions, "edit", True))

    def type_in(self, name: str, value: str) -> None:
        field = tagged(self.page.dialog, "field", name)
        field.value = value
        field.on_change(None)


@pytest.fixture
def world() -> World:
    return World()


@given("a flight AF 718 with gate unknown")
def flight(world: World) -> None:
    assert "departureGate" not in FLIGHT["reservationFor"]


@given("the flight editor")
def editor(world: World) -> None:
    world.open_editor()


@when('the user sets gate "K32" and saves')
def set_gate(world: World) -> None:
    world.open_editor()
    world.type_in("departure_gate", "K32")
    click(button(world.page.dialog, "Save"))


@when("the arrival is set before the departure in UTC")
def arrival_before(world: World) -> None:
    world.type_in("arrival_time", "09:20")  # 10:20 in Paris, before the 10:25 departure


@when("the user opens the calendar of the departure date and picks 23 August 2026")
def pick_date(world: World) -> None:
    click(tagged(world.page.dialog, "picker", "departure_date"))
    picker = world.page.dialog
    assert isinstance(picker, ft.DatePicker)
    picker.value = datetime(2026, 8, 23)
    picked(picker)


@then("the departure date field reads 2026-08-23")
def date_read(world: World) -> None:
    world.page.pop_dialog()  # the picker closes itself
    assert tagged(world.page.dialog, "field", "departure_date").value == "2026-08-23"


@then("the flight's detail shows gate K32")
def shows_gate(world: World) -> None:
    assert world.shell.detail is not None
    assert any("Gate K32" in t for t in texts(world.shell.body))


@then('"Save" is disabled with the reason')
def save_disabled(world: World) -> None:
    assert button(world.page.dialog, "Save").disabled
    assert "The arrival must be after the departure." in texts(world.page.dialog)


# --- details ---


def test_the_editor_names_the_airports(world: World) -> None:
    world.open_editor()
    shown = texts(world.page.dialog)
    assert "Edit Flight" in shown
    assert "Departure · CDG" in shown and "Arrival · LHR" in shown


def test_cancel_changes_nothing(world: World) -> None:
    world.open_editor()
    world.type_in("seat", "1A")
    click(button(world.page.dialog, "Cancel"))
    [kept] = asyncio.run(world.store.reservations())
    assert kept.raw == FLIGHT


def test_a_saved_edit_is_stored(world: World) -> None:
    world.open_editor()
    world.type_in("seat", "1A")
    click(button(world.page.dialog, "Save"))
    [kept] = asyncio.run(world.store.reservations())
    seat: dict[str, Any] = kept.raw["reservedTicket"]["ticketedSeat"]
    assert seat["seatNumber"] == "1A"


def test_a_train_has_no_edit_yet(world: World) -> None:
    from escale_flet.demo import LONDON_TRIP

    train = reservation_from_jsonld(LONDON_TRIP[0], ())
    assert train is not None
    world.shell.open_detail(train)
    assert world.page.appbar is not None
    assert not [
        c
        for c in world.page.appbar.actions or []
        if isinstance(c.data, dict) and c.data.get("edit")
    ]


def test_the_date_picker_starts_on_the_field_s_date(world: World) -> None:
    world.open_editor()
    click(tagged(world.page.dialog, "picker", "arrival_date"))
    picker = world.page.dialog
    assert isinstance(picker, ft.DatePicker)
    assert isinstance(picker.value, datetime) and picker.value.date() == LEAVES.date()


def test_a_picked_time_fills_the_field_and_is_checked(world: World) -> None:
    world.open_editor()
    editor = world.page.dialog
    click(tagged(editor, "picker", "arrival_time"))
    picker = world.page.dialog
    assert isinstance(picker, ft.TimePicker)
    assert picker.hour_format == ft.TimePickerHourFormat.H24
    assert picker.value == time(10, 45)
    picker.value = time(9, 20)  # 10:20 in Paris, before the 10:25 departure
    picked(picker)
    assert tagged(editor, "field", "arrival_time").value == "09:20"
    assert button(editor, "Save").disabled


def test_text_fields_have_no_picker(world: World) -> None:
    world.open_editor()
    pickers = [c.data["picker"] for c in walk(world.page.dialog) if _picker(c)]
    assert pickers == [
        "departure_date",
        "departure_time",
        "boarding_time",
        "arrival_date",
        "arrival_time",
    ]


def _picker(c: Any) -> bool:
    return isinstance(getattr(c, "data", None), dict) and "picker" in c.data


def test_the_picked_day_is_read_in_local_time(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Flutter sends the picked day's local midnight in UTC: 23 August in Paris is
    22 August 22:00 UTC. Python and Flutter share the device's zone (not in web mode)."""
    monkeypatch.setenv("TZ", "Europe/Paris")
    pytime.tzset()
    try:
        world.open_editor()
        click(tagged(world.page.dialog, "picker", "departure_date"))
        picker = world.page.dialog
        assert isinstance(picker, ft.DatePicker)
        picker.value = datetime(2026, 8, 22, 22, 0, tzinfo=UTC)
        picked(picker)
        world.page.pop_dialog()
        assert tagged(world.page.dialog, "field", "departure_date").value == "2026-08-23"
    finally:
        monkeypatch.undo()
        pytime.tzset()


def test_the_editor_changes_presentation_once_its_picker_is_closed(world: World) -> None:
    """Flutter does not close a picker from Python: the editor waits for it."""
    world.open_editor()
    click(tagged(world.page.dialog, "picker", "departure_date"))
    picker = world.page.dialog
    assert isinstance(picker, ft.DatePicker)
    world.shell.resize(380)  # a phone turned: the editor is to become a bottom sheet
    assert world.page.dialog is picker and len(world.page.dialogs) == 2
    world.page.pop_dialog()
    handler: Any = picker.on_dismiss
    handler(None)
    assert len(world.page.dialogs) == 1
    assert isinstance(world.page.dialog, ft.BottomSheet)


def test_ok_on_the_picker_also_lets_the_editor_change_presentation(world: World) -> None:
    """Flutter calls ``on_change`` on OK, not ``on_dismiss`` (seen in the web client)."""
    world.open_editor()
    click(tagged(world.page.dialog, "picker", "departure_date"))
    picker = world.page.dialog
    assert isinstance(picker, ft.DatePicker)
    world.shell.resize(380)
    world.page.pop_dialog()
    picker.value = datetime(2026, 8, 23)
    picked(picker)
    assert isinstance(world.page.dialog, ft.BottomSheet) and len(world.page.dialogs) == 1
    assert tagged(world.page.dialog, "field", "departure_date").value == "2026-08-23"
