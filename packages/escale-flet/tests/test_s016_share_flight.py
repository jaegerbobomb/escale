"""S016 — Share a flight to follow it live."""

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
from escale_flet.testing import FakePage, button

scenarios("S016.feature")


def with_flight(airline: str, number: str) -> dict[str, Any]:
    target = {**FLIGHT["reservationFor"], "flightNumber": number}
    target["airline"] = {"@type": "Airline", "iataCode": airline}
    return {**FLIGHT, "reservationFor": target}


@dataclass
class World:
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    shared: list[str] = field(default_factory=list)
    shell: Shell | None = None

    def open_detail(self, element: dict[str, Any], leaves: str) -> Shell:
        store = InMemoryReservationStore()
        r = reservation_from_jsonld(element, ("d",))
        assert r is not None
        asyncio.run(store.add(Document("d", "t.pdf", "application/pdf"), [r]))
        start = datetime.fromisoformat(leaves)

        async def share(text: str) -> str | None:
            self.shared.append(text)
            return "Link copied"

        self.shell = Shell(store=store, clock=lambda: start - timedelta(hours=2), share=share)
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        assert self.shell.trip is not None
        self.shell.open_detail(self.shell.trip.reservations[0])
        return self.shell


def run(handler: Any) -> None:
    outcome = handler(None)
    if asyncio.iscoroutine(outcome):
        asyncio.run(outcome)


@pytest.fixture
def world() -> World:
    return World()


@given("a flight segment AF 718")
def flight_af718(world: World) -> None:
    world.open_detail(with_flight("AF", "718"), FLIGHT["reservationFor"]["departureTime"])


@given("a train segment")
def train_segment(world: World) -> None:
    world.open_detail(LONDON_TRIP[0], LONDON_TRIP[0]["reservationFor"]["departureTime"])


@given("a flight segment ZZ 12 of an airline missing from the table")
def unknown_airline(world: World) -> None:
    world.open_detail(with_flight("ZZ", "12"), FLIGHT["reservationFor"]["departureTime"])


@when("the user shares it")
def shares(world: World) -> None:
    assert world.shell is not None
    run(button(world.shell.body, "Share flight").on_click)


@then("the shared text holds a Flightradar24 link for AFR718")
def link_shared(world: World) -> None:
    [text] = world.shared
    assert "https://www.flightradar24.com/AFR718" in text


@then('no "Share flight" action is shown')
def no_share(world: World) -> None:
    assert world.shell is not None
    with pytest.raises(LookupError):
        button(world.shell.body, "Share flight")


# --- details ---


def test_sharing_confirms_with_a_snack_bar(world: World) -> None:
    flight_af718(world)
    shares(world)
    assert isinstance(world.page.dialog, ft.SnackBar)


def test_desktop_copies_the_link_mobile_uses_the_share_sheet() -> None:
    from escale_flet.shell import shares_with_sheet

    assert shares_with_sheet(ft.PagePlatform.ANDROID)
    assert shares_with_sheet(ft.PagePlatform.IOS)
    assert not shares_with_sheet(ft.PagePlatform.LINUX)
