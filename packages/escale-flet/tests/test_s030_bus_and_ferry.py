"""S030 — Bus and ferry editors: added by hand, or corrected from the detail."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from datetime import datetime
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.shell import Shell, Tab
from escale_flet.testing import FakePage, button, click, tagged, texts

scenarios("S030.feature")

NOW = datetime.fromisoformat("2027-06-01T09:00:00+02:00")


@pytest.fixture(autouse=True)
def paris(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TZ", "Europe/Paris")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


class World:
    def __init__(self) -> None:
        self.page = FakePage(width=1000)
        self.store = InMemoryReservationStore()
        self.shell = Shell(store=self.store, clock=lambda: NOW)
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())

    def add(self, kind: str) -> None:
        [menu] = [c for c in self.shell.add_button.controls if isinstance(c, ft.PopupMenuButton)]
        [item] = [i for i in menu.items if cast(ft.Text, i.content).value == "Add manually…"]
        click(item)
        click(tagged(self.page.dialog, "manual_kind", kind))

    def type_in(self, name: str, value: str) -> None:
        field = tagged(self.page.dialog, "field", name)
        field.value = value
        field.on_change(None)

    def fill(self, **values: str) -> None:
        for name, value in values.items():
            self.type_in(name, value)


@pytest.fixture
def world() -> World:
    return World()


@given("an empty trip list")
def empty(world: World) -> None:
    assert asyncio.run(world.store.reservations()) == ()


@given("the empty editor of a new bus")
def new_bus_editor(world: World) -> None:
    world.add("bus")


def _trip(world: World, kind: str, start: str, end: str, leave: str, reach: str) -> None:
    world.add(kind)
    world.fill(
        departure_name=start,
        departure_date="2027-07-08",
        departure_time=leave,
        arrival_name=end,
        arrival_date="2027-07-08",
        arrival_time=reach,
    )
    click(button(world.page.dialog, "Save"))


@when("the user adds a bus from Paris Bercy 08:00 to Lyon Perrache 13:00")
def add_bus(world: World) -> None:
    _trip(world, "bus", "Paris Bercy", "Lyon Perrache", "08:00", "13:00")


@when("the user adds a ferry from Calais 10:00 to Dover 10:30")
def add_ferry(world: World) -> None:
    _trip(world, "ferry", "Calais", "Dover", "10:00", "10:30")


@when("the user fills only the departure time")
def departure_only(world: World) -> None:
    world.fill(departure_date="2027-07-08", departure_time="08:00")


def _shows(world: World, town: str, kind: str, *times: str) -> None:
    [booking] = asyncio.run(world.store.reservations())
    assert booking.type == kind and booking.subject_of == ()
    assert world.page.dialog is None
    shown = world.shell._shown()
    assert world.shell.selected == Tab.CURRENT
    assert shown is not None and shown.name == town
    assert world.shell.detail == booking
    body = texts(world.shell.body)
    assert all(t in body for t in times), body


@then("a trip to Lyon shows a bus segment with those times")
def bus_shown(world: World) -> None:
    _shows(world, "Lyon Perrache", "BusReservation", "08:00", "13:00")


@then("a trip to Dover shows a ferry segment with those times")
def ferry_shown(world: World) -> None:
    _shows(world, "Dover", "BoatReservation", "10:00", "10:30")


@then('"Save" is insensitive')
def save_insensitive(world: World) -> None:
    assert button(world.page.dialog, "Save").disabled


@then("the editor says the departure and arrival stops are required")
def stops_required(world: World) -> None:
    shown = texts(world.page.dialog)
    assert "The departure stop is required." in shown
    assert "The arrival stop is required." in shown
    assert "The departure time is required." not in shown


# --- details ---

IMPORTED: dict[str, Any] = {
    "@type": "BoatReservation",
    "reservationNumber": "PO123",
    "reservationFor": {
        "@type": "BoatTrip",
        "departureTime": "2027-07-08T10:00:00+02:00",
        "arrivalTime": "2027-07-08T10:30:00+01:00",
        "departureBoatTerminal": {"@type": "BoatTerminal", "name": "Calais"},
        "arrivalBoatTerminal": {
            "@type": "BoatTerminal",
            "name": "Dover",
            "address": {"@type": "PostalAddress", "addressLocality": "Dover"},
        },
    },
}


def _imported(world: World) -> None:
    r = reservation_from_jsonld(IMPORTED, ("d",))
    assert r is not None
    asyncio.run(world.store.add(Document("d", "p.pdf", "application/pdf"), [r]))
    asyncio.run(world.shell.refresh())
    assert world.shell.trip is not None
    world.shell.open_detail(world.shell.trip.reservations[0])
    assert world.page.appbar is not None
    click(tagged(world.page.appbar.actions, "edit", True))


def test_an_imported_ferry_opens_its_editor_on_its_fields(world: World) -> None:
    _imported(world)
    dialog = world.page.dialog
    assert "Edit Ferry" in texts(dialog)
    assert tagged(dialog, "field", "arrival_city").value == "Dover"
    assert tagged(dialog, "field", "arrival_time").value == "10:30"  # Dover's own time
    for missing in ("seat", "bus_number", "departure_platform"):
        with pytest.raises(LookupError):
            tagged(dialog, "field", missing)


def test_correcting_a_ferry_keeps_its_document_and_zone(world: World) -> None:
    _imported(world)
    world.fill(arrival_time="10:45", arrival_postal_code="CT17 9TF")
    click(button(world.page.dialog, "Save"))
    [ferry] = asyncio.run(world.store.reservations())
    trip = ferry.raw["reservationFor"]
    assert trip["arrivalTime"] == "2027-07-08T10:45:00+01:00"
    assert trip["arrivalBoatTerminal"]["address"]["postalCode"] == "CT17 9TF"
    assert ferry.subject_of == ("d",)
    assert world.page.dialog is None


def test_the_bus_editor_has_kde_s_sections(world: World) -> None:
    world.add("bus")
    shown = texts(world.page.dialog)
    assert "New Bus" in shown
    for title in ("Bus", "Departure", "Departure stop address", "Arrival", "Seat", "Booking"):
        assert title in shown
    for name in ("bus_number", "departure_platform", "arrival_latitude", "seat", "under_name"):
        assert tagged(world.page.dialog, "field", name).value == ""
