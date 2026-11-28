"""S035 — "My trips": cards, filter, search, and a trip opened as a pushed page."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import cast

import flet as ft

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import LONDON_TRIP, MORE_TRIPS
from escale_flet.shell import Shell, Tab
from escale_flet.testing import FakePage, click, tagged, texts, walk

START = datetime.fromisoformat(LONDON_TRIP[0]["reservationFor"]["departureTime"])


def shell_at(width: int = 1000) -> tuple[Shell, FakePage]:
    store = InMemoryReservationStore()
    found = [reservation_from_jsonld(e, ()) for e in [*LONDON_TRIP, *MORE_TRIPS]]
    asyncio.run(store.add(Document("d", "d.pdf", "application/pdf"), [r for r in found if r]))
    shell = Shell(store=store, clock=lambda: START - timedelta(minutes=40))
    page = FakePage(width=width)
    shell.mount(cast(ft.Page, page))
    asyncio.run(shell.refresh())
    shell.select(Tab.TRIPS)
    return shell, page


def cards(shell: Shell) -> list[str]:
    return [
        c.data["trip_card"]
        for c in _walk(shell.body)
        if isinstance(c.data, dict) and "trip_card" in c.data
    ]


def _walk(control: object) -> list[ft.Control]:
    return list(walk(control))


def test_upcoming_then_past_by_year() -> None:
    shell, _ = shell_at()
    sections = [
        c.data["section"]
        for c in _walk(shell.body)
        if isinstance(c.data, dict) and "section" in c.data
    ]
    assert sections == ["Upcoming", "2026", "2025"]
    assert cards(shell) == [
        "London",
        "Concert at the Philharmonie + Le Grand Café",
        "Lisbon",
        "Geneva",
        "Barcelona",
    ]


def test_outings_filter() -> None:
    shell, _ = shell_at()
    shell._on_trip_kind("outing")
    assert cards(shell) == ["Concert at the Philharmonie + Le Grand Café"]


def test_search_keeps_the_entry_and_lists_what_matches() -> None:
    shell, _ = shell_at()
    entry = tagged(shell.body, "trip_search")
    shell._on_trip_query("QX7RTB")
    assert tagged(shell.body, "trip_search") is entry  # not rebuilt: focus stays
    assert cards(shell) == ["Concert at the Philharmonie + Le Grand Café"]
    shell._on_trip_query("nowhere")
    assert "No trip matches." in texts(shell.body)


def test_a_card_opens_the_trip_as_a_pushed_page_and_back_returns() -> None:
    shell, page = shell_at(width=500)
    lisbon = tagged(shell.body, "trip_card", "Lisbon")
    lisbon.on_click(None)
    assert shell.browsed is not None and shell.browsed.name == "Lisbon"
    assert page.navigation_bar is None  # the tabs give way to a back button (ADR-0007)
    assert texts(shell.appbar.title) == ["Lisbon"]
    back = shell.appbar.leading
    assert isinstance(back, ft.IconButton) and back.data == {"back": "trips"}
    click(back)
    assert shell.browsed is None
    assert "Lisbon" in cards(shell)
    assert page.navigation_bar is not None


def test_a_segment_of_an_opened_trip_opens_its_detail_and_back_goes_to_the_trip() -> None:
    shell, page = shell_at()
    assert shell.trip is not None
    shell.open_trip(shell.trip)
    shell.open_detail(shell.trip.reservations[1])
    assert shell.detail is not None
    assert page.navigation_bar is None
    asyncio.run(shell.close_detail())
    assert shell.detail is None and shell.browsed is not None


def test_columns_follow_the_width() -> None:
    shell, _ = shell_at(width=1000)
    assert shell._columns() == 3
    shell.resize(700)
    assert shell._columns() == 2
    shell.resize(380)
    assert shell._columns() == 1


def test_without_trips_the_empty_page_stays() -> None:
    shell = Shell(store=InMemoryReservationStore())
    shell.mount(cast(ft.Page, FakePage(width=1000)))
    asyncio.run(shell.refresh())
    shell.select(Tab.TRIPS)
    assert "No trips yet" in texts(shell.body)
