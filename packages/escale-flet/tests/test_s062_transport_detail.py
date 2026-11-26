"""S062 — Transport detail looks like the mockup."""

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
from escale_flet.demo import FLIGHT, LONDON_TRIP
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, action, tagged, texts, walk

scenarios("S062.feature")


def run(handler: Any) -> None:
    outcome = handler(None)
    if asyncio.iscoroutine(outcome):
        asyncio.run(outcome)


@dataclass
class World:
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    shell: Shell | None = None

    def open(self, element: dict[str, Any], ref: str) -> Shell:
        store = InMemoryReservationStore()
        r = reservation_from_jsonld(element, ("d",))
        assert r is not None
        asyncio.run(store.add(Document("d", "t.pdf", "application/pdf"), [r]))
        leaves = datetime.fromisoformat(element["reservationFor"]["departureTime"])
        self.shell = Shell(store=store, clock=lambda: leaves - timedelta(hours=2))
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        run(tagged(self.shell.body, "segment", ref).on_click)
        return self.shell


@pytest.fixture
def world() -> World:
    return World()


@given("a flight AF 718 from Paris Charles de Gaulle at 10:25 to London Heathrow at 10:45")
def flight(world: World) -> None:
    pass


@when("the user opens its detail")
def opens(world: World) -> None:
    world.open(FLIGHT, "ESC-F718")


@then("the departure and arrival times are shown large with their airports")
def times_large(world: World) -> None:
    assert world.shell is not None
    departure = tagged(world.shell.body, "stop", "departure")
    arrival = tagged(world.shell.body, "stop", "arrival")
    assert "10:25" in texts(departure) and "Paris Charles de Gaulle" in texts(departure)
    assert "10:45" in texts(arrival) and "London Heathrow" in texts(arrival)
    [time] = [c for c in walk(departure) if isinstance(c, ft.Text) and c.value == "10:25"]
    assert time.size == 22


@then('"Show Ticket" is the only suggested button, below the details')
def ticket_below(world: World) -> None:
    assert world.shell is not None
    body = list(walk(world.shell.body))
    suggested = [c for c in body if type(c) is ft.FilledButton]
    assert [c.content for c in suggested] == ["Show Ticket"]
    assert body.index(suggested[0]) > body.index(
        tagged(world.shell.body, "row", "Booking reference")
    )


# --- details ---


def test_identity_chips_and_time_zones_of_a_train(world: World) -> None:
    shell = world.open(LONDON_TRIP[0], "ESC-T1")
    shown = texts(shell.body)
    for expected in ("IC 9014", "Train", "Platform 4", "Coach 12 · Seat 41", "2 h 29"):
        assert expected in shown, expected
    # Paris (+02:00) to London (+01:00): each time says its zone.
    assert "UTC+2" in texts(tagged(shell.body, "stop", "departure"))
    assert "UTC+1" in texts(tagged(shell.body, "stop", "arrival"))


def test_same_zone_shows_no_zone(world: World) -> None:
    element = {
        **FLIGHT,
        "reservationFor": {**FLIGHT["reservationFor"], "arrivalTime": "2026-09-14T11:45:00+02:00"},
    }
    shell = world.open(element, "ESC-F718")
    assert not [t for t in texts(shell.body) if t.startswith("UTC")]


def test_flight_keeps_share_as_a_row(world: World) -> None:
    shell = world.open(FLIGHT, "ESC-F718")
    assert action(shell.body, "Share flight").on_click is not None
    assert "Flight" in texts(shell.body)
