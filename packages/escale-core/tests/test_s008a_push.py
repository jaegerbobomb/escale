"""S008a — local reservations sent to the calendar, on the fake Nextcloud; the real one
is in ``test_nextcloud_dav.py``."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.account import Account
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.extraction import Document, ExtractedReservation
from escale_core.ical_mapping import entries_in
from escale_core.importer import reservation_from_jsonld
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.sqlite_store import SqliteReservationStore
from escale_core.stays import edited, fields_of
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.sync import Sync

scenarios("S008a.feature")

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


@dataclass
class World:
    settings: SettingsFile
    server: FakeNextcloud = field(default_factory=lambda: FakeNextcloud(["Personal"]))
    store: ReservationStore = field(default_factory=InMemoryReservationStore)
    account: Account | None = None

    def connect(self) -> None:
        self.account = Account(self.settings, MemoryPasswords(True), lambda *_: self.server)
        assert asyncio.run(self.account.connect("cloud.example.org", "jane", "pw"))
        asyncio.run(self.account.choose(self.account.calendars[0]))

    def sync(self) -> Sync:
        assert self.account is not None
        return Sync(self.store, self.account)

    def calendar(self) -> list[dict[str, Any]]:
        events = self.server.events.get(self.server.calendar_url("Personal"), {})
        return [
            dict(r.raw)
            for ics, _ in events.values()
            for e in entries_in(ics)
            for r in e.reservations
        ]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(SettingsFile(tmp_path / "settings.json"))


@given("a device connected to a calendar")
def connected(world: World) -> None:
    world.connect()


@given("a device without network")
def offline(world: World) -> None:
    world.connect()
    asyncio.run(world.store.add(DOC, [hotel()]))
    asyncio.run(world.sync().run())
    world.server.reachable = False


@given("a device with no Nextcloud account")
def no_account(world: World) -> None:
    world.account = Account(world.settings, MemoryPasswords(True), lambda *_: world.server)


@when("a reservation is saved on the device")
def saved(world: World) -> None:
    asyncio.run(world.store.add(DOC, [hotel()]))
    asyncio.run(world.sync().run())


@when("the user edits a reservation")
def edit(world: World) -> None:
    [old] = asyncio.run(world.store.reservations())
    new = edited(old, replace(fields_of(old), check_out_time="12:00"))
    asyncio.run(world.store.replace(old, new))
    asyncio.run(world.sync().run())


@when("the network comes back")
def back(world: World) -> None:
    world.server.reachable = True
    asyncio.run(world.sync().run())


@then("the calendar has an event holding that reservation")
def on_calendar(world: World) -> None:
    assert world.calendar() == [HOTEL]


@then("the edit is on the server")
def edit_on_server(world: World) -> None:
    [stay] = world.calendar()
    assert stay["checkoutTime"] == "2026-07-10T12:00:00+01:00"


@then("the reservation is kept on the device only")
def local_only(world: World) -> None:
    assert world.server.events == {}
    assert len(asyncio.run(world.store.reservations())) == 1
    assert len(asyncio.run(world.store.unsent())) == 1


# --- details ---


@pytest.fixture(params=["memory", "sqlite"])
def store(request: pytest.FixtureRequest, tmp_path: Path) -> ReservationStore:
    if request.param == "sqlite":
        return SqliteReservationStore(tmp_path / "data")
    return InMemoryReservationStore()


def test_a_sent_reservation_is_not_sent_again(world: World, store: ReservationStore) -> None:
    world.store = store
    world.connect()
    asyncio.run(store.add(DOC, [hotel()]))
    first = asyncio.run(world.sync().run())
    again = asyncio.run(world.sync().run())
    assert (first.sent, again.sent) == (1, 0)
    assert asyncio.run(store.unsent()) == ()


def test_an_edit_keeps_the_event(world: World, store: ReservationStore) -> None:
    world.store = store
    world.connect()
    asyncio.run(store.add(DOC, [hotel()]))
    asyncio.run(world.sync().run())
    [old] = asyncio.run(store.reservations())
    asyncio.run(store.replace(old, edited(old, replace(fields_of(old), name="The Hoxton"))))
    [outgoing] = asyncio.run(store.unsent())
    assert outgoing.uid is not None and outgoing.etag is not None
    asyncio.run(world.sync().run())
    events = world.server.events[world.server.calendar_url("Personal")]
    assert list(events) == [outgoing.uid]
    assert world.calendar()[0]["reservationFor"]["name"] == "The Hoxton"


def test_the_sync_state_survives_a_restart(world: World, tmp_path: Path) -> None:
    world.store = SqliteReservationStore(tmp_path / "data")
    world.connect()
    asyncio.run(world.store.add(DOC, [hotel()]))
    asyncio.run(world.sync().run())
    world.store = SqliteReservationStore(tmp_path / "data")
    assert asyncio.run(world.store.unsent()) == ()


def test_without_a_chosen_calendar_nothing_is_sent(world: World) -> None:
    world.account = Account(world.settings, MemoryPasswords(True), lambda *_: world.server)
    asyncio.run(world.account.connect("cloud.example.org", "jane", "pw"))
    asyncio.run(world.store.add(DOC, [hotel()]))
    assert asyncio.run(world.sync().run()).sent == 0
    assert world.server.events == {}


def test_a_changed_event_is_not_overwritten(world: World) -> None:
    """S008c since: the server's version is kept, and the run says so."""
    world.connect()
    asyncio.run(world.store.add(DOC, [hotel()]))
    asyncio.run(world.sync().run())
    [old] = asyncio.run(world.store.reservations())
    world.server.touch_all()  # someone else edited it: the known ETag is stale
    asyncio.run(world.store.replace(old, edited(old, replace(fields_of(old), name="X"))))
    report = asyncio.run(world.sync().run())
    assert [r.raw for r in report.changed_elsewhere] == [HOTEL]
    assert asyncio.run(world.store.unsent()) == ()
    assert world.calendar() == [HOTEL]


def test_a_reservation_without_date_is_skipped(world: World) -> None:
    world.connect()
    undated = reservation_from_jsonld({"@type": "FoodEstablishmentReservation"}, ())
    assert undated is not None
    asyncio.run(world.store.add(DOC, [undated, hotel()]))
    assert asyncio.run(world.sync().run()).sent == 1


def test_runs_do_not_overlap(world: World) -> None:
    world.connect()
    asyncio.run(world.store.add(DOC, [hotel()]))
    sync = world.sync()

    async def twice() -> tuple[int, int]:
        a, b = await asyncio.gather(sync.run(), sync.run())
        return a.sent, b.sent

    assert sorted(asyncio.run(twice())) == [0, 1]
