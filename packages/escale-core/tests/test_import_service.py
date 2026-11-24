"""Import service: preview without writing, save only on confirmation (S004)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.importer import Importer
from escale_core.store import InMemoryReservationStore

DATA = Path(__file__).parent / "data"
TRAIN = json.loads((DATA / "train-booking.extracted.json").read_text(encoding="utf-8"))


def test_preview_writes_nothing() -> None:
    store = InMemoryReservationStore()
    importer = Importer(FakeExtractor(TRAIN), store)
    result = asyncio.run(importer.preview(DATA / "train-booking.html"))
    assert len(result.reservations) == 1
    assert asyncio.run(store.reservations()) == ()


def test_confirm_saves_the_reservations_and_their_document() -> None:
    store = InMemoryReservationStore()
    importer = Importer(FakeExtractor(TRAIN), store)
    result = asyncio.run(importer.preview(DATA / "train-booking.html"))
    asyncio.run(importer.confirm(result))
    assert asyncio.run(store.reservations()) == result.reservations
    assert result.document is not None
    assert asyncio.run(store.documents()) == (result.document,)


def test_confirming_an_empty_or_failed_result_saves_nothing() -> None:
    store = InMemoryReservationStore()
    importer = Importer(FakeExtractor([]), store)
    result = asyncio.run(importer.preview(DATA / "no-reservation.pdf"))
    asyncio.run(importer.confirm(result))
    assert asyncio.run(store.reservations()) == ()
    assert asyncio.run(store.documents()) == ()


def test_same_document_is_stored_once() -> None:
    store = InMemoryReservationStore()
    importer = Importer(FakeExtractor(TRAIN), store)
    for _ in range(2):
        asyncio.run(importer.confirm(asyncio.run(importer.preview(DATA / "train-booking.html"))))
    assert len(asyncio.run(store.documents())) == 1
