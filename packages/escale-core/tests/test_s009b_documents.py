"""S009b — ticket documents downloaded on demand and ahead for the current trip, on the
fake Nextcloud; the real one is in ``test_nextcloud_dav.py``."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.account import Account
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.documents import Documents, folder
from escale_core.extraction import Document, ExtractedReservation
from escale_core.importer import reservation_from_jsonld
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.sqlite_store import SqliteReservationStore
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.sync import Sync

scenarios("S009b.feature")


def pdf(n: int) -> tuple[Document, bytes]:
    content = f"%PDF-1.7\n{n}\r\n\x00%%EOF\n".encode()
    return Document(
        hashlib.sha256(content).hexdigest(), f"ticket-{n}.pdf", "application/pdf"
    ), content


def train(n: int, document: Document) -> ExtractedReservation:
    r = reservation_from_jsonld(
        {
            "@type": "TrainReservation",
            "reservationNumber": f"T{n}",
            "reservationFor": {
                "@type": "TrainTrip",
                "departureTime": f"2026-07-0{n}T09:00:00+01:00",
                "arrivalTime": f"2026-07-0{n}T11:00:00+01:00",
                "departureStation": {"@type": "TrainStation", "name": "London"},
                "arrivalStation": {"@type": "TrainStation", "name": "Paris"},
            },
        },
        (document.id,),
    )
    assert r is not None
    return r


@dataclass
class Device:
    store: ReservationStore
    sync: Sync
    documents: Documents
    tmp: Path

    def run(self) -> Any:
        return asyncio.run(self.sync.run())

    def opened(self, r: ExtractedReservation) -> bytes | None:
        path = asyncio.run(self.documents.local(r.subject_of[0]))
        return path.read_bytes() if path else None


class World:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp = tmp_path
        self.server = FakeNextcloud(["Personal"], {"Escale"})
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
        device = Device(store, Sync(store, account), Documents(store, account), where)
        self.devices.append(device)
        return device

    def import_on(self, device: Device, n: int) -> ExtractedReservation:
        document, content = pdf(n)
        source = device.tmp / document.name
        source.write_bytes(content)
        r = train(n, document)
        asyncio.run(device.store.add(document, [r], source))
        return r


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


@given("a ticket imported on Linux with its PDF", target_fixture="ticket")
def imported_on_linux(world: World) -> ExtractedReservation:
    linux = world.device()
    r = world.import_on(linux, 1)
    linux.run()
    world.device().run()  # Android
    return r


@given("a current trip with two ticket PDFs on the server", target_fixture="tickets")
def two_on_server(world: World) -> list[ExtractedReservation]:
    linux = world.device()
    found = [world.import_on(linux, 1), world.import_on(linux, 2)]
    linux.run()
    return found


@given("the device has synced once")
def synced_once(world: World) -> None:
    phone = world.device()
    phone.run()
    asyncio.run(phone.documents.prefetch(asyncio.run(phone.store.reservations())))


@when("the user opens that ticket on Android", target_fixture="shown")
def open_on_android(world: World, ticket: ExtractedReservation) -> bytes | None:
    return world.devices[1].opened(ticket)


@when("the device goes offline")
def offline(world: World) -> None:
    world.server.reachable = False


@then("the PDF is shown")
def pdf_shown(shown: bytes | None) -> None:
    assert shown == pdf(1)[1]


@then("both PDFs open")
def both_open(world: World, tickets: list[ExtractedReservation]) -> None:
    phone = world.devices[-1]
    assert [phone.opened(r) for r in tickets] == [pdf(1)[1], pdf(2)[1]]


# --- details ---


@pytest.fixture(params=["memory", "sqlite"])
def make_store(request: pytest.FixtureRequest, tmp_path: Path) -> Any:
    counter = iter(range(10))

    def make() -> ReservationStore:
        if request.param == "sqlite":
            return SqliteReservationStore(tmp_path / f"data-{next(counter)}")
        return InMemoryReservationStore()

    return make


def test_a_downloaded_document_is_kept_and_not_uploaded_back(world: World, make_store: Any) -> None:
    linux, phone = world.device(make_store()), world.device(make_store())
    r = world.import_on(linux, 1)
    linux.run()
    phone.run()
    assert phone.opened(r) == pdf(1)[1]
    world.server.reachable = False
    assert phone.opened(r) == pdf(1)[1]  # now on the device
    world.server.reachable = True
    world.server.uploads = 0
    phone.run()
    assert world.server.uploads == 0
    [document] = asyncio.run(phone.store.documents())
    assert document == pdf(1)[0]


def test_offline_a_missing_document_is_not_there(world: World) -> None:
    linux, phone = world.device(), world.device()
    r = world.import_on(linux, 1)
    linux.run()
    phone.run()
    world.server.reachable = False
    assert phone.opened(r) is None


def test_a_document_not_uploaded_yet_is_not_there(world: World) -> None:
    phone = world.device()
    document, _ = pdf(1)
    assert asyncio.run(phone.documents.local(document.id)) is None


def test_a_document_that_does_not_match_its_id_is_not_kept(world: World) -> None:
    linux, phone = world.device(), world.device()
    r = world.import_on(linux, 1)
    linux.run()
    phone.run()
    document, _ = pdf(1)
    world.server.files[f"{folder(document.id)}/{document.name}"] = b"tampered"
    assert phone.opened(r) is None
    assert phone.store.document_path(document.id) is None


def test_without_an_account_nothing_is_downloaded(world: World, tmp_path: Path) -> None:
    store = InMemoryReservationStore()
    account = Account(
        SettingsFile(tmp_path / "none.json"), MemoryPasswords(True), lambda *_: world.server
    )
    documents = Documents(store, account)
    assert asyncio.run(documents.local("0" * 64)) is None
    assert asyncio.run(documents.prefetch([])) == 0


def test_prefetch_downloads_only_what_is_missing(world: World) -> None:
    linux, phone = world.device(), world.device()
    found = [world.import_on(linux, 1), world.import_on(linux, 2)]
    linux.run()
    phone.run()
    assert asyncio.run(phone.documents.prefetch(found)) == 2
    assert asyncio.run(phone.documents.prefetch(found)) == 0


def test_prefetch_stops_quietly_without_network(world: World) -> None:
    linux, phone = world.device(), world.device()
    found = [world.import_on(linux, 1)]
    linux.run()
    phone.run()
    world.server.reachable = False
    assert asyncio.run(phone.documents.prefetch(found)) == 0
