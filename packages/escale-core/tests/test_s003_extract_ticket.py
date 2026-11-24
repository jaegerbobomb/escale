"""S003 — Extract a ticket with kitinerary.

The scenarios run the import service with a fake extractor that returns what the real
`kitinerary-extractor` printed for `data/train-booking.html`; the real binary is
exercised in `test_kitinerary_cli.py`.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.adapters.kitinerary_cli import KitineraryCli
from escale_core.extraction import ExtractionResult
from escale_core.importer import Extractor, extract

DATA = Path(__file__).parent / "data"
TRAIN_TICKET = DATA / "train-booking.html"
TRAIN_JSONLD: list[dict[str, Any]] = json.loads(
    (DATA / "train-booking.extracted.json").read_text(encoding="utf-8")
)

scenarios("S003.feature")


@dataclass
class World:
    file: Path | None = None
    extractor: Extractor | None = None
    result: ExtractionResult | None = field(default=None)


@pytest.fixture
def world() -> World:
    return World()


@given("a train ticket that kitinerary-extractor understands")
def a_train_ticket(world: World) -> None:
    world.file = TRAIN_TICKET
    world.extractor = FakeExtractor(TRAIN_JSONLD)


@given("a PDF that contains no reservation")
def a_pdf_without_reservation(world: World) -> None:
    world.file = DATA / "no-reservation.pdf"
    world.extractor = FakeExtractor([])


@given("no kitinerary-extractor is available")
def no_extractor(world: World, tmp_path: Path) -> None:
    world.file = TRAIN_TICKET
    world.extractor = KitineraryCli(search_path=str(tmp_path), fallbacks=())


@when("a file is extracted")
@when("the file is extracted")
def the_file_is_extracted(world: World) -> None:
    assert world.file is not None and world.extractor is not None
    world.result = asyncio.run(extract(world.file, world.extractor))


def _result(world: World) -> ExtractionResult:
    assert world.result is not None
    return world.result


@then("one train reservation is returned with departure and arrival stations and times")
def one_train_reservation(world: World) -> None:
    result = _result(world)
    assert result.error is None
    assert len(result.reservations) == 1
    reservation = result.reservations[0]
    assert reservation.type == "TrainReservation"
    assert reservation.departure is not None and reservation.arrival is not None
    assert reservation.departure.name == "Lyon Part-Dieu"
    assert reservation.arrival.name == "Paris Gare de Lyon"
    assert reservation.departure.time == datetime.fromisoformat("2027-03-14T08:04:00+01:00")
    assert reservation.arrival.time == datetime.fromisoformat("2027-03-14T10:00:00+01:00")


@then("its raw JSON-LD is kept unchanged")
def raw_unchanged(world: World) -> None:
    assert _result(world).reservations[0].raw == TRAIN_JSONLD[0]


@then("no reservation is returned")
def no_reservation(world: World) -> None:
    assert _result(world).reservations == ()


@then("the result says that nothing was recognised")
def nothing_recognised(world: World) -> None:
    result = _result(world)
    assert result.nothing_recognised
    assert result.error is None


@then("the result is an error saying the extractor is not installed")
def extractor_not_installed(world: World) -> None:
    result = _result(world)
    assert result.reservations == ()
    assert not result.nothing_recognised
    assert result.error is not None
    assert "not installed" in result.error


@then("the reservation's subjectOf contains the SHA-256 of the file")
def subject_of_has_sha256(world: World) -> None:
    result = _result(world)
    digest = hashlib.sha256(TRAIN_TICKET.read_bytes()).hexdigest()
    assert result.document is not None
    assert result.document.id == digest
    assert digest in result.reservations[0].subject_of
