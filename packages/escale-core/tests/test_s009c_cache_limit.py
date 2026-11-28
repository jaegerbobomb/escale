"""S009c — the documents of past trips leave the device over the size limit."""

from __future__ import annotations

import asyncio
import hashlib
from datetime import datetime
from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.account import Account
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.documents import LIMIT_BYTES, Documents
from escale_core.extraction import Document, ExtractedReservation
from escale_core.importer import reservation_from_jsonld
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.sqlite_store import SqliteReservationStore
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.sync import Sync
from escale_core.trips import group

scenarios("S009c.feature")

NOW = datetime.fromisoformat("2026-07-15T10:00:00+01:00")  # on the 09:00 train


def train(day: str, ref: str, document: Document) -> ExtractedReservation:
    r = reservation_from_jsonld(
        {
            "@type": "TrainReservation",
            "reservationNumber": ref,
            "reservationFor": {
                "@type": "TrainTrip",
                "departureTime": f"{day}T09:00:00+01:00",
                "arrivalTime": f"{day}T11:00:00+01:00",
                "departureStation": {"@type": "TrainStation", "name": "London"},
                "arrivalStation": {"@type": "TrainStation", "name": "Paris"},
            },
        },
        (document.id,),
    )
    assert r is not None
    return r


class Device:
    def __init__(self, tmp: Path, store: ReservationStore | None = None) -> None:
        self.tmp = tmp
        self.server = FakeNextcloud(["Personal"], {"Escale"})
        self.account = Account(
            SettingsFile(tmp / "settings.json"), MemoryPasswords(True), lambda *_: self.server
        )
        assert asyncio.run(self.account.connect("cloud.example.org", "jane", "pw"))
        asyncio.run(self.account.choose(self.account.calendars[0]))
        self.store = store or InMemoryReservationStore()
        self.documents = Documents(self.store, self.account)
        self.trains: dict[str, ExtractedReservation] = {}

    def ticket(self, day: str, ref: str, size: int = 100) -> ExtractedReservation:
        content = ref.encode() * (size // len(ref))
        document = Document(hashlib.sha256(content).hexdigest(), f"{ref}.pdf", "application/pdf")
        source = self.tmp / document.name
        source.write_bytes(content)
        r = train(day, ref, document)
        asyncio.run(self.store.add(document, [r], source))
        self.trains[ref] = r
        return r

    def sync(self) -> None:
        asyncio.run(Sync(self.store, self.account).run())

    def clean(self, limit: int) -> int:
        trips = group(asyncio.run(self.store.reservations()))
        return asyncio.run(self.documents.clean(trips, NOW, limit))

    def here(self, ref: str) -> bool:
        return self.store.document_path(self.trains[ref].subject_of[0]) is not None


@pytest.fixture
def device(tmp_path: Path) -> Device:
    return Device(tmp_path)


@given("a device over its document limit with a past trip and a future trip")
def over_limit(device: Device) -> None:
    device.ticket("2026-06-01", "PAST")
    device.ticket("2026-08-01", "NEXT")
    device.sync()


@given("a past trip whose document was removed from the device")
def removed(device: Device) -> None:
    over_limit(device)
    assert device.clean(limit=150) == 1


@when("the device cleans its documents")
def cleans(device: Device) -> None:
    device.clean(limit=150)


@when("the user opens that document with network", target_fixture="shown")
def opens(device: Device) -> bytes | None:
    path = asyncio.run(device.documents.local(device.trains["PAST"].subject_of[0]))
    return path.read_bytes() if path else None


@then("the past trip's documents are removed from the device")
def past_removed(device: Device) -> None:
    assert not device.here("PAST")


@then("the future trip's documents are kept")
def future_kept(device: Device) -> None:
    assert device.here("NEXT")


@then("the document is shown")
def shown_again(shown: bytes | None) -> None:
    assert shown == b"PAST" * 25


# --- details ---


@pytest.fixture(params=["memory", "sqlite"])
def any_device(request: pytest.FixtureRequest, tmp_path: Path) -> Device:
    if request.param == "sqlite":
        return Device(tmp_path, SqliteReservationStore(tmp_path / "data"))
    return Device(tmp_path)


def test_the_default_limit_is_500_mb() -> None:
    assert LIMIT_BYTES == 500 * 1024 * 1024


def test_under_the_limit_nothing_is_removed(any_device: Device) -> None:
    any_device.ticket("2026-06-01", "PAST")
    any_device.sync()
    assert any_device.clean(limit=1000) == 0
    assert any_device.here("PAST")


def test_the_oldest_trip_goes_first_and_only_as_much_as_needed(any_device: Device) -> None:
    any_device.ticket("2026-05-01", "OLDEST")
    any_device.ticket("2026-06-01", "OLDER")
    any_device.sync()
    assert any_device.clean(limit=150) == 1
    assert not any_device.here("OLDEST") and any_device.here("OLDER")


def test_the_current_trip_is_kept(any_device: Device) -> None:
    any_device.ticket("2026-07-15", "TODAY")
    any_device.ticket("2026-06-01", "PAST")
    any_device.sync()
    any_device.clean(limit=0)
    assert any_device.here("TODAY") and not any_device.here("PAST")


def test_a_document_not_on_the_server_yet_is_kept(any_device: Device) -> None:
    any_device.ticket("2026-06-01", "PAST")  # no sync: only on this device
    assert any_device.clean(limit=0) == 0
    assert any_device.here("PAST")


def test_the_imported_file_itself_is_never_deleted(device: Device) -> None:
    """The in-memory store points at the file the user imported: it forgets it only."""
    device.ticket("2026-06-01", "PAST")
    device.sync()
    device.clean(limit=0)
    assert (device.tmp / "PAST.pdf").exists()
    assert not device.here("PAST")


def test_a_removed_document_is_not_uploaded_again(any_device: Device) -> None:
    any_device.ticket("2026-06-01", "PAST")
    any_device.sync()
    any_device.clean(limit=0)
    any_device.server.uploads = 0
    any_device.sync()
    assert any_device.server.uploads == 0


def test_the_sqlite_copy_is_deleted_from_disk(tmp_path: Path) -> None:
    device = Device(tmp_path, SqliteReservationStore(tmp_path / "data"))
    r = device.ticket("2026-06-01", "PAST")
    device.sync()
    folder = tmp_path / "data" / "documents" / r.subject_of[0]
    assert folder.is_dir()
    device.clean(limit=0)
    assert not folder.exists()


def test_without_an_account_nothing_is_removed(tmp_path: Path) -> None:
    """No server to download it again from: a document stays."""
    store = InMemoryReservationStore()
    account = Account(
        SettingsFile(tmp_path / "s.json"), MemoryPasswords(True), lambda *_: FakeNextcloud()
    )
    documents = Documents(store, account)
    content = b"x" * 100
    document = Document(hashlib.sha256(content).hexdigest(), "a.pdf", "application/pdf")
    (tmp_path / "a.pdf").write_bytes(content)
    asyncio.run(store.add(document, [train("2026-06-01", "A", document)], tmp_path / "a.pdf"))
    asyncio.run(store.document_sent(document.id))
    trips = group(asyncio.run(store.reservations()))
    assert asyncio.run(documents.clean(trips, NOW, 0)) == 0
