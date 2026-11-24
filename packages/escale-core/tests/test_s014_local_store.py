"""S014 — Local store in SQLite."""

from __future__ import annotations

import asyncio
import hashlib
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.importer import Importer
from escale_core.sqlite_store import SCHEMA_VERSION, SqliteReservationStore

DATA = Path(__file__).parent / "data"
TRAIN_JSONLD: list[dict[str, Any]] = json.loads(
    (DATA / "train-booking.extracted.json").read_text(encoding="utf-8")
)

scenarios("S014.feature")


@dataclass
class World:
    root: Path
    digest: str = ""
    ticket: Path = field(init=False)
    store: SqliteReservationStore = field(init=False)

    def __post_init__(self) -> None:
        self.ticket = self.root / "inbox" / "train-booking.html"
        self.ticket.parent.mkdir(parents=True)
        shutil.copy(DATA / "train-booking.html", self.ticket)
        self.store = self.open()

    def open(self) -> SqliteReservationStore:
        return SqliteReservationStore(self.root / "data")

    def import_ticket(self) -> None:
        importer = Importer(FakeExtractor(TRAIN_JSONLD), self.store)
        asyncio.run(importer.confirm(asyncio.run(importer.preview(self.ticket))))


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


@given("a confirmed import of a train ticket")
def confirmed_import(world: World) -> None:
    world.import_ticket()


@when("the app is closed and opened again")
def reopen(world: World) -> None:
    world.store.close()
    world.store = world.open()


@when("the original file is deleted")
def delete_original(world: World) -> None:
    world.digest = hashlib.sha256(world.ticket.read_bytes()).hexdigest()
    world.ticket.unlink()


@when("the same file is imported and confirmed again")
def import_again(world: World) -> None:
    world.import_ticket()


@then("the reservation is still saved")
def still_saved(world: World) -> None:
    [reservation] = asyncio.run(world.store.reservations())
    assert reservation.type == "TrainReservation"
    assert reservation.raw == TRAIN_JSONLD[0]
    assert reservation.departure is not None
    assert reservation.departure.name == "Lyon Part-Dieu"


@then("the document is still available under its SHA-256")
def document_kept(world: World) -> None:
    digest = world.digest
    path = world.store.document_path(digest)
    assert path is not None
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    meta = json.loads((path.parent / "meta.json").read_text(encoding="utf-8"))
    assert meta == {
        "@type": "DigitalDocument",
        "name": "train-booking.html",
        "encodingFormat": "text/html",
    }


@then("the reservation is saved once")
def saved_once(world: World) -> None:
    assert len(asyncio.run(world.store.reservations())) == 1
    assert len(asyncio.run(world.store.documents())) == 1


# --- details ---


def test_schema_version_is_recorded(tmp_path: Path) -> None:
    store = SqliteReservationStore(tmp_path)
    asyncio.run(store.reservations())
    assert store.schema_version() == SCHEMA_VERSION


def test_opening_does_not_create_anything_until_used(tmp_path: Path) -> None:
    SqliteReservationStore(tmp_path / "data")
    assert not (tmp_path / "data").exists()


def test_same_reservation_from_another_file_is_not_duplicated(world: World) -> None:
    world.import_ticket()
    other = world.root / "inbox" / "confirmation-email.html"
    other.write_text("<html>another copy of the booking</html>", encoding="utf-8")
    importer = Importer(FakeExtractor(TRAIN_JSONLD), world.store)
    asyncio.run(importer.confirm(asyncio.run(importer.preview(other))))
    [reservation] = asyncio.run(world.store.reservations())
    assert len(asyncio.run(world.store.documents())) == 2
    assert len(reservation.subject_of) == 2


def test_reservations_without_reference_nor_time_are_told_apart_by_content(world: World) -> None:
    a = {"@type": "EventReservation", "reservationFor": {"@type": "Event", "name": "A"}}
    b = {"@type": "EventReservation", "reservationFor": {"@type": "Event", "name": "B"}}
    importer = Importer(FakeExtractor([a, b]), world.store)
    asyncio.run(importer.confirm(asyncio.run(importer.preview(world.ticket))))
    assert len(asyncio.run(world.store.reservations())) == 2


def test_a_new_extraction_of_the_same_booking_is_not_duplicated(world: World) -> None:
    """kitinerary stamps each run with a new ``modifiedTime``: that is not a new booking."""
    world.import_ticket()
    later = [{**TRAIN_JSONLD[0], "modifiedTime": "2027-03-02T09:00:00"}]
    importer = Importer(FakeExtractor(later), world.store)
    asyncio.run(importer.confirm(asyncio.run(importer.preview(world.ticket))))
    assert len(asyncio.run(world.store.reservations())) == 1
