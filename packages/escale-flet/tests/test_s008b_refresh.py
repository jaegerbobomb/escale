"""S008b — what the calendar sent shows without restarting the app."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import cast

import flet as ft

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_core.sync import SyncReport
from escale_flet.demo import LONDON_TRIP
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, texts

HOTEL = LONDON_TRIP[1]
CHECK_IN = datetime.fromisoformat(HOTEL["checkinTime"])


def test_a_received_reservation_appears() -> None:
    store = InMemoryReservationStore()
    hotel = reservation_from_jsonld(HOTEL, ())
    assert hotel is not None

    async def sync() -> SyncReport:  # another device sent the hotel meanwhile
        await store.add(Document("d", "b.pdf", "application/pdf"), [hotel])
        return SyncReport(received=1)

    shell = Shell(store=store, clock=lambda: CHECK_IN - timedelta(hours=1), sync=sync)
    shell.mount(cast(ft.Page, FakePage(width=1000)))
    asyncio.run(shell.refresh())
    assert shell.trip is None
    asyncio.run(shell.synchronise())
    assert shell.trip is not None
    assert "The Hoxton, Holborn" in texts(shell.body)


def test_a_detail_removed_elsewhere_closes() -> None:
    store = InMemoryReservationStore()
    hotel = reservation_from_jsonld(HOTEL, ())
    assert hotel is not None
    asyncio.run(store.add(Document("d", "b.pdf", "application/pdf"), [hotel]))

    async def sync() -> SyncReport:
        store._rows.clear()  # the event was deleted from the calendar
        return SyncReport(received=1)

    shell = Shell(store=store, clock=lambda: CHECK_IN - timedelta(hours=1), sync=sync)
    shell.mount(cast(ft.Page, FakePage(width=1000)))
    asyncio.run(shell.refresh())
    assert shell.trip is not None
    shell.open_detail(shell.trip.reservations[0])
    asyncio.run(shell.synchronise())
    assert shell.detail is None and shell.trip is None


def test_nothing_received_leaves_the_view_alone() -> None:
    calls: list[str] = []

    async def sync() -> SyncReport:
        return SyncReport()

    shell = Shell(sync=sync)
    page = FakePage(width=1000)
    shell.mount(cast(ft.Page, page))
    before = page.updates
    asyncio.run(shell.synchronise())
    assert page.updates == before and calls == []
