"""S021 — Shortcut to the current ticket."""

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
from escale_flet.testing import FakePage, button, click

scenarios("S021.feature")

LEAVES = datetime.fromisoformat(LONDON_TRIP[0]["reservationFor"]["departureTime"])


@dataclass
class World:
    store: InMemoryReservationStore = field(default_factory=InMemoryReservationStore)
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    shell: Shell | None = None

    def keep(self, elements: list[dict[str, Any]], documents: tuple[str, ...]) -> None:
        found = [reservation_from_jsonld(e, documents) for e in elements]
        asyncio.run(
            self.store.add(Document("d", "t.pdf", "application/pdf"), [r for r in found if r])
        )

    def show(self) -> Shell:
        self.shell = Shell(store=self.store, clock=lambda: LEAVES - timedelta(minutes=40))
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        return self.shell


def without_ticket(element: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in element.items() if k != "reservedTicket"}


@pytest.fixture
def world() -> World:
    return World()


@given("a current trip whose next train has a ticket")
def next_has_ticket(world: World) -> None:
    world.keep(LONDON_TRIP, ("d",))


@given("a current trip whose next segment has no ticket")
def next_has_none(world: World) -> None:
    world.keep([without_ticket(e) for e in LONDON_TRIP], ())


@when('the user presses "Show ticket"')
def press(world: World) -> None:
    click(button(world.show().body, "Show ticket"))


@when('the "Current" tab is shown')
def shown(world: World) -> None:
    world.show()


@then("that train's ticket is shown full screen")
def ticket_shown(world: World) -> None:
    assert world.shell is not None and world.shell.ticket is not None
    assert world.shell.ticket.reference == "ESC-T1"
    assert world.page.navigation_bar is None


@then('there is no "Show ticket" button')
def no_button(world: World) -> None:
    assert world.shell is not None
    with pytest.raises(LookupError):
        button(world.shell.body, "Show ticket")
