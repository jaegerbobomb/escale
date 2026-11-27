"""S009a — ticket documents sent to Nextcloud and linked from the events, on the fake
Nextcloud; the real one is in ``test_nextcloud_dav.py``."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.account import Account
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.documents import folder, jsonld, split
from escale_core.extraction import Document, ExtractedReservation
from escale_core.ical_mapping import entries_in, from_event, new_entry, to_event
from escale_core.importer import reservation_from_jsonld
from escale_core.nextcloud import ServerUnreachable
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.sqlite_store import SqliteReservationStore
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.sync import Sync

scenarios("S009a.feature")

HOTEL: dict[str, Any] = {
    "@type": "LodgingReservation",
    "reservationNumber": "ESC-H1",
    "checkinTime": "2026-07-08T15:00:00+01:00",
    "checkoutTime": "2026-07-10T11:00:00+01:00",
    "reservationFor": {"@type": "LodgingBusiness", "name": "The Hoxton, Holborn"},
}
PDF = b"%PDF-1.7\n\x00\x01binary\r\nline\n%%EOF\n"
DOC = Document(hashlib.sha256(PDF).hexdigest(), "booking.pdf", "application/pdf")


def hotel(subject_of: tuple[str, ...] = (DOC.id,)) -> ExtractedReservation:
    r = reservation_from_jsonld(HOTEL, subject_of)
    assert r is not None
    return r


@dataclass
class Device:
    store: ReservationStore
    sync: Sync
    tmp: Path

    def run(self) -> Any:
        return asyncio.run(self.sync.run())

    def import_ticket(self) -> None:
        source = self.tmp / "booking.pdf"
        source.write_bytes(PDF)
        asyncio.run(self.store.add(DOC, [hotel()], source))


class World:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        self.server = FakeNextcloud(["Personal"], {"Escale"})
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
        where = self.tmp / f"device-{n}"
        where.mkdir()
        device = Device(store, Sync(store, account), where)
        self.devices.append(device)
        return device

    def event_reservations(self) -> list[dict[str, Any]]:
        return [
            dict(r.raw) | {"subjectOf": list(r.subject_of)}
            for ics, _ in self.server.events[self.calendar].values()
            for e in entries_in(ics)
            for r in e.reservations
        ]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


@given("a device connected to a calendar")
def connected(world: World) -> None:
    world.device()


@given("two devices connected to the same calendar")
def two_devices(world: World) -> None:
    world.device()
    world.device()


@given("a PDF already present on the server")
def already_there(world: World) -> None:
    first = world.device()
    first.import_ticket()
    first.run()
    world.server.uploads = 0


@when("a ticket is imported with its PDF")
def imported(world: World) -> None:
    world.devices[0].import_ticket()


@when("a ticket is imported with its PDF on the first device")
def imported_on_first(world: World) -> None:
    world.devices[0].import_ticket()


@when("the same PDF is imported again on another device")
def imported_elsewhere(world: World) -> None:
    world.device().import_ticket()


@when("the device syncs")
def device_syncs(world: World) -> None:
    world.devices[0].run()


@when("that device syncs")
def that_device_syncs(world: World) -> None:
    world.devices[-1].run()


@when("both devices sync")
def both_sync(world: World) -> None:
    for device in world.devices:
        device.run()


@then("the server has the PDF and its meta.json in the document's folder")
def on_server(world: World) -> None:
    where = folder(DOC.id)
    assert world.server.files[f"{where}/booking.pdf"] == PDF
    meta = json.loads(world.server.files[f"{where}/meta.json"])
    assert meta == {
        "@type": "DigitalDocument",
        "name": "booking.pdf",
        "encodingFormat": "application/pdf",
    }


@then("the calendar event names that document in subjectOf")
def named_in_event(world: World) -> None:
    [element] = world.event_reservations()
    assert element["subjectOf"] == [DOC.id]


@then("no file is uploaded")
def nothing_uploaded(world: World) -> None:
    assert world.server.uploads == 0


@then("the second device's reservation names that document")
def second_names_it(world: World) -> None:
    [shown] = asyncio.run(world.devices[1].store.reservations())
    assert shown.subject_of == (DOC.id,)


# --- details ---


@pytest.fixture(params=["memory", "sqlite"])
def make_store(request: pytest.FixtureRequest, tmp_path: Path) -> Any:
    counter = iter(range(10))

    def make() -> ReservationStore:
        if request.param == "sqlite":
            return SqliteReservationStore(tmp_path / f"data-{next(counter)}")
        return InMemoryReservationStore()

    return make


def test_the_document_is_uploaded_once(world: World, make_store: Any) -> None:
    device = world.device(make_store())
    device.import_ticket()
    assert device.run().uploaded == 1
    assert device.run().uploaded == 0
    assert world.server.uploads == 2  # the file, then meta.json
    assert asyncio.run(device.store.unsent_documents()) == ()


def test_the_upload_state_survives_a_restart(world: World, tmp_path: Path) -> None:
    device = world.device(SqliteReservationStore(tmp_path / "data"))
    device.import_ticket()
    device.run()
    assert asyncio.run(SqliteReservationStore(tmp_path / "data").unsent_documents()) == ()


def test_meta_json_is_written_last(world: World) -> None:
    device = world.device()
    device.import_ticket()
    device.run()
    assert world.server.written == [f"{folder(DOC.id)}/booking.pdf", f"{folder(DOC.id)}/meta.json"]


def test_no_event_is_sent_before_its_document(
    world: World, monkeypatch: pytest.MonkeyPatch
) -> None:
    device = world.device()
    device.import_ticket()

    async def unreachable(*_: object) -> bool:
        raise ServerUnreachable

    monkeypatch.setattr(world.server, "put_file", unreachable)
    report = device.run()
    assert report.problem is not None and report.sent == 0
    assert world.server.events.get(world.calendar, {}) == {}
    monkeypatch.undo()
    assert device.run().sent == 1
    assert f"{folder(DOC.id)}/meta.json" in world.server.files


def test_a_document_without_a_local_file_does_not_hold_the_event(world: World) -> None:
    device = world.device()
    asyncio.run(device.store.add(DOC, [hotel()]))  # no source: nothing to upload
    report = device.run()
    assert (report.uploaded, report.sent) == (0, 1)


def test_events_written_before_get_their_documents(world: World, make_store: Any) -> None:
    """0.22.0 sent events without ``subjectOf``: their reservations go once more."""
    device = world.device(make_store())
    asyncio.run(device.store.add(DOC, [hotel()]))
    asyncio.run(device.store.sent([hotel(())], "KIT-1", world.calendar + "KIT-1.ics", None))
    [outgoing] = asyncio.run(device.store.unsent())
    assert outgoing.uid == "KIT-1"


def test_a_new_document_of_a_sent_reservation_is_linked(world: World, make_store: Any) -> None:
    device = world.device(make_store())
    asyncio.run(device.store.add(DOC, [hotel()]))
    device.run()
    other = Document("e" * 64, "receipt.pdf", "application/pdf")
    asyncio.run(device.store.add(other, [hotel((other.id,))]))
    assert device.run().sent == 1
    [element] = world.event_reservations()
    assert element["subjectOf"] == [DOC.id, other.id]


def test_documents_received_and_local_are_both_kept(world: World, make_store: Any) -> None:
    first, second = world.device(make_store()), world.device(make_store())
    first.import_ticket()
    other = Document("e" * 64, "receipt.pdf", "application/pdf")
    asyncio.run(second.store.add(other, [hotel((other.id,))]))
    first.run()
    second.run()
    [shown] = asyncio.run(second.store.reservations())
    assert set(shown.subject_of) == {DOC.id, other.id}


def test_subject_of_goes_in_the_event_and_back() -> None:
    entry = new_entry([hotel()])
    payload = json.loads(str(to_event(entry)["X-KDE-KITINERARY-RESERVATION"]))
    assert payload[0]["subjectOf"] == [DOC.id]
    back = from_event(to_event(entry))
    assert back is not None
    [r] = back.reservations
    assert r.subject_of == (DOC.id,) and "subjectOf" not in r.raw


def test_other_things_in_subject_of_are_kept() -> None:
    """``subjectOf`` may hold more than document ids: those stay in the JSON-LD."""
    page = {"@type": "WebPage", "url": "https://example.org"}
    raw, ids = split({**HOTEL, "subjectOf": [page, DOC.id]})
    assert ids == (DOC.id,) and raw["subjectOf"] == [page]
    r = reservation_from_jsonld(raw, ids)
    assert r is not None
    assert jsonld(r)["subjectOf"] == [page, DOC.id]


def test_a_single_id_is_read_too() -> None:
    raw, ids = split({**HOTEL, "subjectOf": DOC.id})
    assert ids == (DOC.id,) and "subjectOf" not in raw


def test_a_version_3_database_is_migrated(tmp_path: Path) -> None:
    """0.22.0 did not know which documents were on the server: all of them go once."""
    import sqlite3

    folder_ = tmp_path / "data"
    store = SqliteReservationStore(folder_)
    source = tmp_path / "booking.pdf"
    source.write_bytes(PDF)
    asyncio.run(store.add(DOC, [hotel()], source))
    store.close()
    db = sqlite3.connect(folder_ / "escale.sqlite")
    db.executescript(
        """
        CREATE TABLE d AS SELECT id, name, mime_type FROM documents;
        DROP TABLE documents;
        ALTER TABLE d RENAME TO documents;
        UPDATE meta SET value = '3' WHERE key = 'schema_version';
        """
    )
    db.commit()
    db.close()
    again = SqliteReservationStore(folder_)
    assert again.schema_version() == 4
    [(document, path)] = asyncio.run(again.unsent_documents())
    assert document == DOC and path.read_bytes() == PDF
