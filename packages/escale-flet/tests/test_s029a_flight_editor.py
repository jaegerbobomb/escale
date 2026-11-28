"""S029a — Edit a flight."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import FLIGHT
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, button, click, tagged, texts

scenarios("S029a.feature")

LEAVES = datetime.fromisoformat(FLIGHT["reservationFor"]["departureTime"])


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
