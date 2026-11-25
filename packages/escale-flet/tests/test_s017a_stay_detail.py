"""S017a — Stay detail."""

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

scenarios("S017a.feature")

HOTEL: dict[str, Any] = LONDON_TRIP[1]
CHECK_IN = datetime.fromisoformat(HOTEL["checkinTime"])


def hotel(**place: Any) -> dict[str, Any]:
    return {**HOTEL, "reservationFor": {**HOTEL["reservationFor"], **place}}


@dataclass
class World:
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    launched: list[str] = field(default_factory=list)
    element: dict[str, Any] = field(default_factory=lambda: HOTEL)
    shell: Shell | None = None

    def open(self) -> Shell:
        store = InMemoryReservationStore()
        r = reservation_from_jsonld(self.element, ("d",))
        assert r is not None
        asyncio.run(store.add(Document("d", "b.pdf", "application/pdf"), [r]))

        async def launch(url: str) -> None:
            self.launched.append(url)

        self.shell = Shell(store=store, clock=lambda: CHECK_IN - timedelta(hours=3), launch=launch)
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        run(card(self.shell, "ESC-H1").on_click)
        return self.shell


def card(shell: Shell, ref: str) -> Any:
    [found] = [
        c for c in walk(shell.body) if isinstance(c.data, dict) and c.data.get("segment") == ref
    ]
    return found


def row(shell: Shell, label: str) -> Any:
    [found] = [
        c for c in walk(shell.body) if isinstance(c.data, dict) and c.data.get("row") == label
    ]
    return found


def run(handler: Any) -> None:
    outcome = handler(None)
    if asyncio.iscoroutine(outcome):
        asyncio.run(outcome)


@pytest.fixture
def world() -> World:
    return World()


@given('a stored stay at "The Hoxton, Holborn" from 8 July 15:00 to 10 July 11:00')
def hoxton(world: World) -> None:
    world.element = HOTEL


@given("a stay imported from a Booking.com confirmation with a link to manage the booking")
def booking_com(world: World) -> None:
    world.element = {
        **HOTEL,
        "potentialAction": {
            "@type": "UpdateAction",
            "target": "https://secure.booking.com/myreservations.html?bn=1",
        },
    }


@given("a stored stay whose hotel has a telephone number")
def with_telephone(world: World) -> None:
    world.element = hotel(telephone="+44 20 7946 0000")


@when("the user opens its card")
@when("the user opens its detail")
def opens(world: World) -> None:
    world.open()


@when("the user opens its detail and taps the telephone")
def taps_telephone(world: World) -> None:
    shell = world.open()
    run(row(shell, "Telephone").on_click)


@then("the detail shows the name, the address, the check-in and the check-out")
def detail_shown(world: World) -> None:
    assert world.shell is not None
    shown = " | ".join(texts(world.shell.body))
    for expected in ("The Hoxton, Holborn", "199-206 High Holborn, London"):
        assert expected in shown, expected
    moments = {
        c.data["moment"]: texts(c)
        for c in walk(world.shell.body)
        if isinstance(c.data, dict) and "moment" in c.data
    }
    assert moments == {
        "Check-in": ["CHECK-IN", "15:00", "Wed 8 July"],
        "Check-out": ["CHECK-OUT", "11:00", "Fri 10 July"],
    }
    assert "2" in texts(world.shell.body) and "nights" in texts(world.shell.body)


@then('a "Manage booking on Booking.com" action is shown')
def manage_shown(world: World) -> None:
    assert world.shell is not None
    run(button(world.shell.body, "Manage booking on Booking.com").on_click)
    assert world.launched == ["https://secure.booking.com/myreservations.html?bn=1"]


@then("the system is asked to call that number")
def calls(world: World) -> None:
    assert world.launched == ["tel:+442079460000"]


# --- details ---


def test_room_contact_and_cancelled_status_are_shown(world: World) -> None:
    world.element = {
        **hotel(email="desk@example.com", url="https://example.com/hotel"),
        "lodgingUnitDescription": "Double room, courtyard",
        "reservationStatus": "http://schema.org/ReservationCancelled",
    }
    shell = world.open()
    shown = texts(shell.body)
    for expected in (
        "Double room, courtyard",
        "desk@example.com",
        "https://example.com/hotel",
        "Cancelled",
    ):
        assert expected in shown, expected
    run(row(shell, "E-mail").on_click)
    run(row(shell, "Website").on_click)
    assert world.launched == ["mailto:desk@example.com", "https://example.com/hotel"]


def test_no_manage_action_without_a_link(world: World) -> None:
    shell = world.open()
    assert not [t for t in texts(shell.body) if t.startswith("Manage booking")]
