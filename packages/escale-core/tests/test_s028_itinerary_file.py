"""S028 — import a KDE Itinerary export (``.itinerary``, a zip; KItinerary's ``File``)."""

from __future__ import annotations

import asyncio
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.extraction import ExtractionResult
from escale_core.importer import Importer
from escale_core.itinerary_file import read_itinerary
from escale_core.sqlite_store import SqliteReservationStore
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.trips import group

scenarios("S028.feature")

PDF_A = b"%PDF-1.7\nLisbon\n"
PDF_B = b"%PDF-1.7\nBerlin\n"
ID_A = hashlib.sha256(PDF_A).hexdigest()
ID_B = hashlib.sha256(PDF_B).hexdigest()


def stay(ref: str, town: str, checkin: str, checkout: str, doc: str) -> dict[str, Any]:
    return {
        "@type": "LodgingReservation",
        "reservationNumber": ref,
        "reservationFor": {
            "@type": "LodgingBusiness",
            "name": f"Hotel {town}",
            "address": {"@type": "PostalAddress", "addressLocality": town},
        },
        "checkinTime": f"{checkin}T15:00:00+02:00",
        "checkoutTime": f"{checkout}T11:00:00+02:00",
        "subjectOf": [doc],
    }


def export(path: Path, extra: dict[str, bytes] | None = None) -> Path:
    """An export laid out as KItinerary's ``File`` writes it."""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "reservations/1b2c.json",
            json.dumps(stay("L1", "Lisbon", "2026-08-22", "2026-08-24", ID_A)),
        )
        # an array of one element is read too (File::reservation)
        z.writestr(
            "reservations/3d4e.json",
            json.dumps([stay("B1", "Berlin", "2026-09-15", "2026-09-18", ID_B)]),
        )
        for doc_id, name, content in ((ID_A, "lisbon.pdf", PDF_A), (ID_B, "berlin.pdf", PDF_B)):
            meta = {"@type": "DigitalDocument", "name": name, "encodingFormat": "application/pdf"}
            z.writestr(f"documents/{doc_id}/meta.json", json.dumps(meta))
            z.writestr(f"documents/{doc_id}/{name}", content)
        for name, data in (extra or {}).items():
            z.writestr(name, data)
    return path


@pytest.fixture
def world(tmp_path: Path) -> dict[str, Any]:
    store = InMemoryReservationStore()
    return {"tmp": tmp_path, "store": store, "importer": Importer(FakeExtractor([]), store)}


def import_file(world: dict[str, Any], path: Path) -> ExtractionResult:
    result: ExtractionResult = asyncio.run(world["importer"].preview(path))
    world["result"] = result
    return result


@given("an `.itinerary` file with two trips and their PDFs")
def a_file(world: dict[str, Any]) -> None:
    world["file"] = export(world["tmp"] / "export.itinerary")


@given("the same `.itinerary` file was already imported")
def imported_once(world: dict[str, Any]) -> None:
    a_file(world)
    asyncio.run(world["importer"].confirm(import_file(world, world["file"])))


@when("the user imports it")
def user_imports(world: dict[str, Any]) -> None:
    import_file(world, world["file"])


@when("it is imported again")
def imported_again(world: dict[str, Any]) -> None:
    asyncio.run(world["importer"].confirm(import_file(world, world["file"])))


@then("the confirmation lists the reservations")
def lists(world: dict[str, Any]) -> None:
    result: ExtractionResult = world["result"]
    assert [r.reference for r in result.reservations] == ["L1", "B1"]
    assert result.error is None


@then("after confirming, both trips appear with their documents")
def both_trips(world: dict[str, Any]) -> None:
    store: ReservationStore = world["store"]
    asyncio.run(world["importer"].confirm(world["result"]))
    trips = group(asyncio.run(store.reservations()))
    assert [t.name for t in trips] == ["Lisbon", "Berlin"]
    path = store.document_path(ID_A)
    assert path is not None and path.read_bytes() == PDF_A


@then("nothing is duplicated")
def not_duplicated(world: dict[str, Any]) -> None:
    store: ReservationStore = world["store"]
    assert len(asyncio.run(store.reservations())) == 2
    assert len(asyncio.run(store.documents())) == 2


# --- details ---


def test_ids_are_kept(tmp_path: Path) -> None:
    result = read_itinerary(export(tmp_path / "e.itinerary"))
    assert [r.subject_of for r in result.reservations] == [(ID_A,), (ID_B,)]
    assert "subjectOf" not in result.reservations[0].raw
    assert sorted((d.name, d.id, d.mime_type) for d, _ in result.documents) == [
        ("berlin.pdf", ID_B, "application/pdf"),
        ("lisbon.pdf", ID_A, "application/pdf"),
    ]


def test_what_is_not_imported_is_listed(tmp_path: Path) -> None:
    extra = {
        "passes/pass.com.example/QUJD.pkpass": b"zip",
        "passes/pass.com.example/REVG.pkpass": b"zip",
        "custom/org.kde.itinerary/programs/p1": b"{}",
        "custom/org.kde.itinerary/health-certificates/c1": b"x",
        "custom/org.kde.itinerary/settings/settings.ini": b"[General]",
        "custom/org.kde.itinerary/trips/t1": b"{}",
    }
    result = read_itinerary(export(tmp_path / "e.itinerary", extra))
    assert result.not_imported == (
        "2 passes",
        "1 program membership",
        "1 health certificate",
        "settings",
    )


def test_a_document_without_its_file_is_left_out(tmp_path: Path) -> None:
    path = tmp_path / "e.itinerary"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(
            "reservations/a.json",
            json.dumps(stay("L1", "Lisbon", "2026-08-22", "2026-08-24", ID_A)),
        )
        z.writestr(f"documents/{ID_A}/meta.json", json.dumps({"name": "missing.pdf"}))
    result = read_itinerary(path)
    assert result.documents == () and len(result.reservations) == 1


def test_not_a_zip_is_an_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.itinerary"
    path.write_bytes(b"not a zip")
    result = read_itinerary(path)
    assert result.error == "broken.itinerary is not a KDE Itinerary export."
    assert result.reservations == ()


def test_an_empty_export_finds_nothing(tmp_path: Path) -> None:
    path = tmp_path / "empty.itinerary"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("custom/org.kde.itinerary/version/version", b"{}")
    assert read_itinerary(path).nothing_recognised


def test_unreadable_reservations_are_skipped(tmp_path: Path) -> None:
    path = tmp_path / "e.itinerary"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("reservations/bad.json", b"{not json")
        z.writestr("reservations/other.json", json.dumps({"@type": "Place", "name": "x"}))
        z.writestr(
            "reservations/ok.json",
            json.dumps(stay("L1", "Lisbon", "2026-08-22", "2026-08-24", ID_A)),
        )
    assert [r.reference for r in read_itinerary(path).reservations] == ["L1"]


def test_documents_are_kept_by_the_sqlite_store_and_uploaded_later(tmp_path: Path) -> None:
    store = SqliteReservationStore(tmp_path / "data")
    importer = Importer(FakeExtractor([]), store)
    result = asyncio.run(importer.preview(export(tmp_path / "e.itinerary")))
    asyncio.run(importer.confirm(result))
    assert {d.id for d, _ in asyncio.run(store.unsent_documents())} == {ID_A, ID_B}
    assert (tmp_path / "data" / "documents" / ID_B / "berlin.pdf").read_bytes() == PDF_B


def test_a_ticket_is_still_read_by_the_extractor(tmp_path: Path) -> None:
    pdf = tmp_path / "ticket.pdf"
    pdf.write_bytes(PDF_A)
    element = stay("L1", "Lisbon", "2026-08-22", "2026-08-24", ID_A)
    importer = Importer(FakeExtractor([element]), InMemoryReservationStore())
    result = asyncio.run(importer.preview(pdf))
    assert result.document is not None and len(result.reservations) == 1
