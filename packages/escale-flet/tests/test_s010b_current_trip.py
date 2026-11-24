"""S010b — Current trip timeline."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import LONDON_TRIP
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, texts, walk

scenarios("S010b.feature")

FIRST_DEPARTURE = datetime.fromisoformat(LONDON_TRIP[0]["reservationFor"]["departureTime"])


@dataclass
class World:
    store: InMemoryReservationStore = field(default_factory=InMemoryReservationStore)
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    now: datetime = FIRST_DEPARTURE - timedelta(days=2)
    shell: Shell | None = None

    def store_all(self, elements: list[dict[str, Any]]) -> None:
        found = [reservation_from_jsonld(e, ("doc",)) for e in elements]
        from escale_core.extraction import Document

        asyncio.run(
            self.store.add(Document("doc", "t.pdf", "application/pdf"), [r for r in found if r])
        )

    def show_current(self) -> Shell:
        self.shell = Shell(store=self.store, clock=lambda: self.now)
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        return self.shell


def cards(shell: Shell) -> list[ft.Control]:
    return [c for c in walk(shell.body) if isinstance(c.data, dict) and "segment" in c.data]


@pytest.fixture
def world() -> World:
    return World()


@given("a stored trip to London with a train, a hotel and a train back")
def london(world: World) -> None:
    world.store_all(LONDON_TRIP)


@given("a current trip whose first train leaves in 40 minutes")
def leaving_soon(world: World) -> None:
    world.store_all(LONDON_TRIP)
    world.now = FIRST_DEPARTURE - timedelta(minutes=40)


@when('the "Current" tab is shown')
def current_shown(world: World) -> None:
    world.show_current()


@then("the three segments are shown in time order under the trip's name")
def three_in_order(world: World) -> None:
    assert world.shell is not None
    shown = texts(world.shell.body)
    assert "London" in shown
    assert [c.data["segment"] for c in cards(world.shell)] == ["ESC-T1", "ESC-H1", "ESC-T2"]


@then("that train's card is highlighted as next")
def next_highlighted(world: World) -> None:
    assert world.shell is not None
    found = cards(world.shell)
    assert [c.data["next"] for c in found] == [True, False, False]
    assert "NEXT · leaves in 40 min" in texts(found[0])


# --- details ---


def test_no_trip_keeps_the_empty_view(world: World) -> None:
    shell = world.show_current()
    assert "No current trip" in texts(shell.body)


def test_header_shows_dates_and_travellers(world: World) -> None:
    world.store_all(LONDON_TRIP)
    shown = texts(world.show_current().body)
    assert "8–10 Jul 2026 · 2 travellers" in shown
    shell = world.shell
    assert shell is not None
    avatars = [
        c.data["avatar"]
        for c in walk(shell.body)
        if isinstance(c.data, dict) and "avatar" in c.data
    ]
    assert avatars == ["Jane Doe", "Alex Martin"]


def test_train_card_shows_times_platform_seat_and_duration(world: World) -> None:
    world.store_all(LONDON_TRIP)
    shell = world.show_current()
    train = " | ".join(texts(cards(shell)[0]))
    for expected in (
        "IC 9014",
        "08:01",
        "Paris Gare du Nord",
        "09:30",
        "London St Pancras",
        "Platform 4",
        "Coach 12 · Seat 41",
        "2 h 29",
    ):
        assert expected in train, expected


def test_hotel_card_shows_nights(world: World) -> None:
    world.store_all(LONDON_TRIP)
    hotel = texts(cards(world.show_current())[1])
    assert "2 nights" in hotel
    assert "The Hoxton, Holborn" in hotel


def test_past_trip_is_not_current(world: World) -> None:
    world.store_all(LONDON_TRIP)
    world.now = FIRST_DEPARTURE + timedelta(days=30)
    assert "No current trip" in texts(world.show_current().body)


def test_refresh_shows_new_reservations(world: World) -> None:
    shell = world.show_current()
    world.store_all(LONDON_TRIP)
    asyncio.run(shell.refresh())
    assert len(cards(shell)) == 3
