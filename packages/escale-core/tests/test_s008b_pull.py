"""S008b — changes received from the calendar, on the fake Nextcloud; the real one is in
``test_nextcloud_dav.py``."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
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
from escale_core.sqlite_store import SCHEMA_VERSION, SqliteReservationStore
from escale_core.stays import edited, fields_of
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.sync import Sync

scenarios("S008b.feature")

DATA = Path(__file__).parent / "data"
HOTEL: dict[str, Any] = {
    "@type": "LodgingReservation",
    "reservationNumber": "ESC-H1",
    "checkinTime": "2026-07-08T15:00:00+01:00",
    "checkoutTime": "2026-07-10T11:00:00+01:00",
    "reservationFor": {"@type": "LodgingBusiness", "name": "The Hoxton, Holborn"},
}
DOC = Document("d", "booking.pdf", "application/pdf")


def hotel(raw: dict[str, Any] = HOTEL) -> ExtractedReservation:
    r = reservation_from_jsonld(raw, ("d",))
    assert r is not None
    return r


@dataclass
class Device:
    store: ReservationStore
    sync: Sync

    def run(self) -> Any:
        return asyncio.run(self.sync.run())

    def shown(self) -> list[str]:
        return [r.raw["reservationFor"]["name"] for r in asyncio.run(self.store.reservations())]


class World:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        self.server = FakeNextcloud(["Personal"])
        self.calendar = self.server.calendar_url("Personal")
        self.devices: list[Device] = []

    def device(self, store: ReservationStore | None = None) -> Device:
        n = len(self.devices)
        account = Account(
            SettingsFile(self.tmp / f"settings-{n}.json"),
            MemoryPasswords(True),
            lambda *_: self.server,
        )
        assert asyncio.run(account.connect("cloud.example.org", "jane", "pw"))
        asyncio.run(account.choose(account.calendars[0]))
        store = store or InMemoryReservationStore()
        device = Device(store, Sync(store, account))
        self.devices.append(device)
        return device


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


@given("two devices connected to the same calendar")
def two_devices(world: World) -> None:
    world.device()
    world.device()


@given("two devices showing the same reservation")
def two_showing(world: World) -> None:
    first, second = world.device(), world.device()
    asyncio.run(first.store.add(DOC, [hotel()]))
    first.run()
    second.run()
    assert second.shown() == ["The Hoxton, Holborn"]


@given("a calendar where KDE Itinerary wrote a hotel stay")
def kde_wrote(world: World) -> None:
    ics = (DATA / "kitinerary-hotel.ics").read_bytes()
    asyncio.run(world.server.put_event(world.calendar + "kde-1.ics", ics, None))
    world.device()


@when("a reservation is saved on the first device")
def saved_on_first(world: World) -> None:
    asyncio.run(world.devices[0].store.add(DOC, [hotel()]))
    world.devices[0].run()


@when("its event is deleted from the calendar")
def deleted(world: World) -> None:
    world.server.delete_all()


@when("the second device syncs")
def second_syncs(world: World) -> None:
    world.devices[1].run()


@when("the device syncs")
def device_syncs(world: World) -> None:
    world.devices[0].run()


@then("the second device shows the reservation")
def second_shows(world: World) -> None:
    assert world.devices[1].shown() == ["The Hoxton, Holborn"]


@then("the second device no longer shows it")
def second_does_not_show(world: World) -> None:
    assert world.devices[1].shown() == []


@then("the device shows the stay")
def shows_stay(world: World) -> None:
    assert world.devices[0].shown() == ["Glo Hotel Sello"]


# --- details ---


@pytest.fixture(params=["memory", "sqlite"])
def make_store(request: pytest.FixtureRequest, tmp_path: Path) -> Any:
    counter = iter(range(10))

    def make() -> ReservationStore:
        if request.param == "sqlite":
            return SqliteReservationStore(tmp_path / f"data-{next(counter)}")
        return InMemoryReservationStore()

    return make


def test_an_edit_made_elsewhere_replaces_the_local_copy(world: World, make_store: Any) -> None:
    first, second = world.device(make_store()), world.device(make_store())
    asyncio.run(first.store.add(DOC, [hotel()]))
    first.run()
    second.run()
    [old] = asyncio.run(first.store.reservations())
    asyncio.run(first.store.replace(old, edited(old, replace(fields_of(old), name="The Hoxton"))))
    first.run()
    report = second.run()
    assert report.received == 1
    assert second.shown() == ["The Hoxton"]
    assert asyncio.run(second.store.unsent()) == ()


def test_its_own_events_are_not_received_again(world: World, make_store: Any) -> None:
    device = world.device(make_store())
    asyncio.run(device.store.add(DOC, [hotel()]))
    device.run()
    assert device.run().received == 0
    assert device.shown() == ["The Hoxton, Holborn"]


def test_plain_events_are_ignored(world: World) -> None:
    plain = b"BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:x\r\nSUMMARY:Dentist\r\n"
    plain += b"DTSTART:20260708T090000Z\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    asyncio.run(world.server.put_event(world.calendar + "x.ics", plain, None))
    device = world.device()
    assert device.run().received == 0 and device.shown() == []


def test_a_local_edit_meets_one_made_elsewhere(world: World) -> None:
    """The local change is not sent over the other one; S008c keeps the server's."""
    first, second = world.device(), world.device()
    asyncio.run(first.store.add(DOC, [hotel()]))
    first.run()
    second.run()
    for device, name in ((first, "From the first"), (second, "From the second")):
        [old] = asyncio.run(device.store.reservations())
        new = edited(old, replace(fields_of(old), name=name))
        asyncio.run(device.store.replace(old, new))
    first.run()
    world.server.reachable = True
    report = second.run()
    [kept] = report.changed_elsewhere
    assert kept.raw["reservationFor"]["name"] == "From the first"
    assert second.shown() == ["From the first"]


def test_a_refused_token_starts_over(world: World) -> None:
    first, second = world.device(), world.device()
    asyncio.run(first.store.add(DOC, [hotel()]))
    first.run()
    second.run()
    world.server.delete_all()
    world.server.forget_tokens()  # the server lost its history: full listing
    second.run()
    assert second.shown() == []


def test_the_token_survives_a_restart(world: World, tmp_path: Path) -> None:
    device = world.device(SqliteReservationStore(tmp_path / "data"))
    asyncio.run(device.store.add(DOC, [hotel()]))
    device.run()
    again = SqliteReservationStore(tmp_path / "data")
    assert asyncio.run(again.calendar_token(world.calendar)) is not None


def test_a_batch_from_kde_itinerary_is_sent_back_whole(world: World) -> None:
    other = {**HOTEL, "underName": {"@type": "Person", "name": "Alex"}}
    from escale_core.ical_mapping import entries_in, new_entry, to_ics

    batch = new_entry([hotel(), hotel(other)])
    asyncio.run(world.server.put_event(world.calendar + "batch.ics", to_ics([batch]), None))
    device = world.device()
    device.run()
    assert len(device.shown()) == 2
    [first, _] = asyncio.run(device.store.reservations())
    edited_first = edited(first, replace(fields_of(first), name="Renamed"))
    asyncio.run(device.store.replace(first, edited_first))
    device.run()
    events = world.server.events[world.calendar]
    [entry] = entries_in(events["batch"][0])
    assert len(entry.reservations) == 2
    assert entry.reservations[0].raw["reservationFor"]["name"] == "Renamed"


def test_a_version_2_database_is_migrated(tmp_path: Path) -> None:
    """0.20.0 kept the events in a ``calendar_events`` table, keyed by the old identity."""
    import json
    import sqlite3

    folder = tmp_path / "data"
    folder.mkdir()
    db = sqlite3.connect(folder / "escale.sqlite")
    raw = json.dumps(HOTEL)
    old_identity = "LodgingReservation|ESC-H1|"
    db.executescript(
        """
        CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE documents (id TEXT PRIMARY KEY, name TEXT NOT NULL, mime_type TEXT NOT NULL);
        CREATE TABLE reservations (id INTEGER PRIMARY KEY, identity TEXT NOT NULL UNIQUE,
            raw TEXT NOT NULL, subject_of TEXT NOT NULL);
        CREATE TABLE calendar_events (identity TEXT PRIMARY KEY, uid TEXT NOT NULL,
            href TEXT NOT NULL, etag TEXT, sent TEXT NOT NULL);
        INSERT INTO meta VALUES ('schema_version', '2');
        """
    )
    db.execute(
        "INSERT INTO reservations (identity, raw, subject_of) VALUES (?, ?, '[\"d\"]')",
        (old_identity, raw),
    )
    db.execute(
        "INSERT INTO calendar_events VALUES (?, 'KIT-1', 'https://c/KIT-1.ics', '\"7\"', ?)",
        (old_identity, raw),
    )
    db.commit()
    db.close()
    store = SqliteReservationStore(folder)
    assert store.schema_version() == SCHEMA_VERSION
    # sent again once, now with its document in ``subjectOf`` (S009a)
    [outgoing] = asyncio.run(store.unsent())
    assert (outgoing.uid, outgoing.href) == ("KIT-1", "https://c/KIT-1.ics")
    assert asyncio.run(store.events()) == {"https://c/KIT-1.ics": '"7"'}
    asyncio.run(store.add(DOC, [hotel()]))  # same booking again: not duplicated
    assert len(asyncio.run(store.reservations())) == 1


def test_a_rate_limited_server_asks_to_try_later(monkeypatch: pytest.MonkeyPatch) -> None:
    """Nextcloud answers 429 when asked too often; that is not "not a Nextcloud"."""
    from caldav.lib import error as dav_error

    from escale_core.adapters.nextcloud_dav import NextcloudDav
    from escale_core.nextcloud import ServerBusy

    server = NextcloudDav("https://cloud.test", "jane", "pw")

    def limited(*_: object, **__: object) -> None:
        raise dav_error.RateLimitError("https://cloud.test/")

    monkeypatch.setattr(server._client, "request", limited)
    with pytest.raises(ServerBusy):
        asyncio.run(server.changes("https://cloud.test/remote.php/dav/calendars/jane/t/", None))
