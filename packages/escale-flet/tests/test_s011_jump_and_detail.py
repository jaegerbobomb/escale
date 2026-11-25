"""S011 — Jump index and segment detail."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import LONDON_TRIP_FULL
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, texts, walk

scenarios("S011.feature")

LEAVES = datetime.fromisoformat(LONDON_TRIP_FULL[0]["reservationFor"]["departureTime"])


@dataclass
class World:
    width: int = 1000
    store: InMemoryReservationStore = field(default_factory=InMemoryReservationStore)
    page: FakePage | None = None
    shell: Shell | None = None

    def open_trip(self) -> Shell:
        found = [reservation_from_jsonld(e, ("d",)) for e in LONDON_TRIP_FULL]
        asyncio.run(
            self.store.add(Document("d", "t.pdf", "application/pdf"), [r for r in found if r])
        )
        self.page = FakePage(width=self.width)
        self.shell = Shell(store=self.store, clock=lambda: LEAVES - timedelta(minutes=40))
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        return self.shell


def segment(shell: Shell, ref: str) -> Any:
    [card] = [
        c for c in walk(shell.body) if isinstance(c.data, dict) and c.data.get("segment") == ref
    ]
    return card


def index_entry(shell: Shell, title: str) -> Any:
    for c in walk(shell.body):
        if isinstance(c.data, dict) and c.data.get("jump") and title in texts(c):
            return c
    raise LookupError(title)


def run(handler: Any) -> None:
    outcome = handler(None)
    if asyncio.iscoroutine(outcome):
        asyncio.run(outcome)


@pytest.fixture
def world() -> World:
    return World()


@given(parsers.parse("a trip with five segments is open in a window {width:d} px wide"))
@given(parsers.parse("a trip is open in a window {width:d} px wide"))
def trip_open_at(world: World, width: int) -> None:
    world.width = width
    world.open_trip()


@given("a trip is open and scrolled to its return train")
def scrolled_to_return(world: World) -> None:
    shell = world.open_trip()
    asyncio.run(shell.jump("ESC-T2"))


@when(parsers.parse('the user clicks "{title}" in the jump index'))
def click_index(world: World, title: str) -> None:
    assert world.shell is not None
    run(index_entry(world.shell, title).on_click)


@when("the user opens the return train's detail")
def open_return(world: World) -> None:
    assert world.shell is not None
    run(segment(world.shell, "ESC-T2").on_click)


@when("the user opens a segment's detail")
def open_any(world: World) -> None:
    assert world.shell is not None
    run(segment(world.shell, "ESC-H1").on_click)


@when("goes back to the trip")
def go_back(world: World) -> None:
    assert world.shell is not None
    [back] = [c for c in walk(world.shell.body) if isinstance(c.data, dict) and c.data.get("back")]
    run(back.on_click)


@then("the timeline scrolls to the Tate Modern card and highlights it")
def scrolled_to_tate(world: World) -> None:
    assert world.shell is not None
    assert world.shell.scroll_target == "ESC-E1"
    assert segment(world.shell, "ESC-E1").data["highlighted"]


@then("the timeline is still shown")
def timeline_shown(world: World) -> None:
    assert world.shell is not None and world.shell.detail is None
    assert (
        len([c for c in walk(world.shell.body) if isinstance(c.data, dict) and "segment" in c.data])
        == 5
    )


@then("the timeline is scrolled to the return train card")
def scrolled_to_return_card(world: World) -> None:
    assert world.shell is not None and world.shell.detail is None
    assert world.shell.scroll_target == "ESC-T2"


@then("that card is highlighted")
def return_highlighted(world: World) -> None:
    assert world.shell is not None
    assert segment(world.shell, "ESC-T2").data["highlighted"]


@then("the jump index panel is not shown")
def no_panel(world: World) -> None:
    assert world.shell is not None
    assert not [
        c for c in walk(world.shell.body) if isinstance(c.data, dict) and c.data.get("jump_panel")
    ]


@then('a "Jump to…" action is available')
def jump_menu(world: World) -> None:
    assert world.shell is not None
    menus = [
        c
        for c in walk(world.shell.body)
        if isinstance(c, ft.PopupMenuButton) and c.tooltip == "Jump to…"
    ]
    assert menus and len(menus[0].items) == 5


@then("the bottom navigation bar is hidden")
def bar_hidden(world: World) -> None:
    assert world.page is not None and world.shell is not None
    assert world.shell.detail is not None
    assert world.page.navigation_bar is None


# --- details ---


def test_wide_window_has_the_index_panel(world: World) -> None:
    shell = world.open_trip()
    [panel] = [c for c in walk(shell.body) if isinstance(c.data, dict) and c.data.get("jump_panel")]
    assert "Tate Modern" in texts(panel)


def test_detail_shows_the_segment_and_a_back_button_named_after_the_trip(world: World) -> None:
    shell = world.open_trip()
    run(segment(shell, "ESC-T1").on_click)
    shown = texts(shell.body)
    for expected in ("London", "IC 9014", "Paris Gare du Nord", "London St Pancras", "ESC-T1"):
        assert expected in " | ".join(shown), expected


def test_medium_window_detail_keeps_the_tabs(world: World) -> None:
    world.width = 500
    shell = world.open_trip()
    run(segment(shell, "ESC-H1").on_click)
    assert world.page is not None and world.page.navigation_bar is not None


def test_narrow_window_index_is_a_bottom_sheet(world: World) -> None:
    world.width = 380
    shell = world.open_trip()
    [button] = [
        c for c in walk(shell.body) if isinstance(c.data, dict) and c.data.get("jump_sheet")
    ]
    run(button.on_click)
    assert world.page is not None
    assert isinstance(world.page.dialog, ft.BottomSheet)
    assert "Tate Modern" in texts(world.page.dialog)
