"""S008c — a conflicting edit keeps the server version."""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.account import Account
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.extraction import Document, ExtractedReservation
from escale_core.importer import reservation_from_jsonld
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.sqlite_store import SqliteReservationStore
from escale_core.stays import edited, fields_of
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.sync import Sync, SyncReport

scenarios("S008c.feature")

HOTEL: dict[str, Any] = {
    "@type": "LodgingReservation",
    "reservationNumber": "ESC-H1",
    "checkinTime": "2026-07-08T15:00:00+01:00",
    "checkoutTime": "2026-07-10T11:00:00+01:00",
    "reservationFor": {"@type": "LodgingBusiness", "name": "The Hoxton, Holborn"},
}
DOC = Document("d", "booking.pdf", "application/pdf")


def hotel() -> ExtractedReservation:
    r = reservation_from_jsonld(HOTEL, ("d",))
    assert r is not None
    return r


def names(reservations: Sequence[ExtractedReservation]) -> list[str]:
    return [r.raw["reservationFor"]["name"] for r in reservations]


def rename(store: ReservationStore, name: str) -> None:
    [old] = asyncio.run(store.reservations())
    asyncio.run(store.replace(old, edited(old, replace(fields_of(old), name=name))))


class World:
    def __init__(self, tmp_path: Path, store: ReservationStore | None = None) -> None:
        self.server = FakeNextcloud(["Personal"])
        self.calendar = self.server.calendar_url("Personal")
        self.syncs: list[tuple[ReservationStore, Sync]] = []
        self.tmp = tmp_path
        self.report = SyncReport()
        self.store = store

    def device(self, store: ReservationStore | None = None) -> tuple[ReservationStore, Sync]:
        n = len(self.syncs)
        account = Account(
            SettingsFile(self.tmp / f"{n}.json"), MemoryPasswords(True), lambda *_: self.server
        )
        assert asyncio.run(account.connect("cloud.example.org", "jane", "pw"))
        asyncio.run(account.choose(account.calendars[0]))
        store = store or InMemoryReservationStore()
        self.syncs.append((store, Sync(store, account)))
        return self.syncs[-1]

    def names(self, store: ReservationStore) -> list[str]:
        return [r.raw["reservationFor"]["name"] for r in asyncio.run(store.reservations())]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


@pytest.fixture(params=["memory", "sqlite"])
def stores(request: pytest.FixtureRequest, tmp_path: Path) -> World:
    if request.param == "sqlite":
        return World(tmp_path, SqliteReservationStore(tmp_path / "data"))
    return World(tmp_path)


@given("a reservation edited on the server since the device last synced")
def edited_on_server(world: World) -> None:
    other_store, other = world.device()
    _, sync = world.device(world.store)
    asyncio.run(other_store.add(DOC, [hotel()]))
    asyncio.run(other.run())
    asyncio.run(sync.run())
    rename(other_store, "Renamed elsewhere")
    asyncio.run(other.run())


@when("the device sends its own edit of that reservation")
def sends_own(world: World) -> None:
    store, sync = world.syncs[1]
    rename(store, "Renamed here")
    world.report = asyncio.run(sync.run())


@then("the device shows the server version")
def shows_server(world: World) -> None:
    store, _ = world.syncs[1]
    assert world.names(store) == ["Renamed elsewhere"]
    assert asyncio.run(store.unsent()) == ()


@then("the user is told the reservation changed elsewhere")
def told(world: World) -> None:
    assert names(world.report.changed_elsewhere) == ["Renamed elsewhere"]


# --- details ---


def test_a_change_the_pull_did_not_see_is_caught_at_send(stores: World) -> None:
    """The event changed between the pull and the send: the 412 brings the server's."""
    world = stores
    store, sync = world.device(world.store)
    asyncio.run(store.add(DOC, [hotel()]))
    asyncio.run(sync.run())
    events = world.server.events[world.calendar]
    [(name, (ics, _))] = events.items()
    elsewhere = ics.replace(b"The Hoxton\\, Holborn", b"Changed quietly")
    events[name] = (elsewhere, '"quiet"')  # not in the sync log: the pull misses it
    rename(store, "Renamed here")
    report = asyncio.run(sync.run())
    assert names(report.changed_elsewhere) == ["Changed quietly"]
    assert world.names(store) == ["Changed quietly"]
    assert asyncio.run(store.unsent()) == ()


def test_deleted_elsewhere_while_edited_here(stores: World) -> None:
    world = stores
    store, sync = world.device(world.store)
    asyncio.run(store.add(DOC, [hotel()]))
    asyncio.run(sync.run())
    world.server.delete_all()
    rename(store, "Renamed here")
    report = asyncio.run(sync.run())
    assert names(report.changed_elsewhere) == ["Renamed here"]
    assert asyncio.run(store.reservations()) == ()
