"""S017b — editing a stay (core part): fields, validation, saving."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.sqlite_store import SqliteReservationStore
from escale_core.stays import edited, fields_of, problems
from escale_core.store import InMemoryReservationStore
from escale_core.trips import span

STAY: dict[str, Any] = {
    "@type": "LodgingReservation",
    "reservationNumber": "H-1",
    "underName": {"@type": "Person", "name": "Jane Doe", "email": "jane@example.com"},
    "checkinTime": {
        "@type": "QDateTime",
        "@value": "2026-07-08T15:00:00+01:00",
        "timezone": "Europe/London",
    },
    "checkoutTime": "2026-07-10T11:00:00+01:00",
    "reservationFor": {
        "@type": "LodgingBusiness",
        "name": "Hotel Test",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "1 Test St",
            "addressLocality": "London",
        },
        "telephone": "+44 20 7946 0000",
    },
}


def stay() -> Any:
    r = reservation_from_jsonld(STAY, ("d",))
    assert r is not None
    return r


def test_fields_of_a_stay() -> None:
    f = fields_of(stay())
    assert (f.name, f.street, f.city, f.telephone, f.reference, f.under_name) == (
        "Hotel Test",
        "1 Test St",
        "London",
        "+44 20 7946 0000",
        "H-1",
        "Jane Doe",
    )
    assert (f.check_in_date, f.check_in_time) == ("2026-07-08", "15:00")
    assert (f.check_out_date, f.check_out_time) == ("2026-07-10", "11:00")


def test_untouched_fields_give_the_same_json_ld() -> None:
    r = stay()
    assert edited(r, fields_of(r)).raw == r.raw


def test_new_check_out_time_keeps_the_place_time() -> None:
    r = stay()
    new = edited(r, replace(fields_of(r), check_out_time="12:00"))
    assert span(new) is not None
    assert span(new)[1].isoformat() == "2026-07-10T12:00:00+01:00"  # type: ignore[index]
    assert new.raw["checkoutTime"] == "2026-07-10T12:00:00+01:00"


def test_check_in_in_winter_follows_the_place_time_zone() -> None:
    r = stay()
    new = edited(r, replace(fields_of(r), check_in_date="2026-01-08", check_out_date="2026-01-10"))
    assert new.raw["checkinTime"] == {
        "@type": "QDateTime",
        "@value": "2026-01-08T15:00:00+00:00",
        "timezone": "Europe/London",
    }


def test_edited_fields_reach_the_json_ld() -> None:
    r = stay()
    f = replace(
        fields_of(r),
        name="Hotel Renamed",
        postal_code="WC1V 7BD",
        latitude="51.5",
        longitude="-0.12",
        description="Twin room",
        email="desk@example.com",
        telephone="",
        reference="H-2",
        under_name="Alex Martin",
    )
    new = edited(r, f)
    place = new.raw["reservationFor"]
    assert place["name"] == "Hotel Renamed"
    assert place["address"]["postalCode"] == "WC1V 7BD"
    assert place["geo"] == {"@type": "GeoCoordinates", "latitude": 51.5, "longitude": -0.12}
    assert place["email"] == "desk@example.com"
    assert "telephone" not in place
    assert new.raw["lodgingUnitDescription"] == "Twin room"
    assert new.raw["underName"] == {"@type": "Person", "name": "Alex Martin"}
    assert new.reference == "H-2"


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"name": "  "}, "The name is required."),
        ({"check_in_date": ""}, "The check-in is required."),
        ({"check_out_time": "25:00"}, "The check-out is not a valid date and time."),
        ({"check_out_date": "2026-07-07"}, "The check-out must be after the check-in."),
        ({"latitude": "91"}, "The coordinates are not valid."),
        ({"latitude": "51.5"}, "The coordinates are not valid."),
    ],
)
def test_problems(changes: dict[str, str], message: str) -> None:
    assert problems(replace(fields_of(stay()), **changes)) == [message]


def test_no_problem_for_the_stay_as_it_is() -> None:
    assert problems(fields_of(stay())) == []


@pytest.mark.parametrize("kind", ["memory", "sqlite"])
def test_store_replaces_a_reservation(kind: str, tmp_path: Path) -> None:
    store = InMemoryReservationStore() if kind == "memory" else SqliteReservationStore(tmp_path)
    r = stay()
    asyncio.run(store.add(Document("d", "b.pdf", "application/pdf"), [r]))
    new = edited(r, replace(fields_of(r), reference="H-2", check_out_time="12:00"))
    asyncio.run(store.replace(r, new))
    [kept] = asyncio.run(store.reservations())
    assert kept.reference == "H-2"
    assert kept.raw["checkoutTime"] == "2026-07-10T12:00:00+01:00"
    assert kept.subject_of == ("d",)
