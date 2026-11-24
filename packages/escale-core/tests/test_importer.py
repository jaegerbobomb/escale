"""Mapping kitinerary's JSON-LD to extracted reservations."""

from __future__ import annotations

import asyncio
import copy
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.importer import extract, parse_datetime

TICKET = Path(__file__).parent / "data" / "no-reservation.pdf"


def _extract(*elements: dict[str, Any]) -> Any:
    return asyncio.run(extract(TICKET, FakeExtractor(list(elements))))


def test_datetime_as_qdatetime_object() -> None:
    value = {
        "@type": "QDateTime",
        "@value": "2019-09-06T15:45:00+02:00",
        "timezone": "Europe/Vienna",
    }
    assert parse_datetime(value) == datetime(2019, 9, 6, 15, 45, tzinfo=ZoneInfo("Europe/Vienna"))


def test_naive_datetime_takes_the_given_timezone() -> None:
    value = {"@type": "QDateTime", "@value": "2027-03-14T08:04:00", "timezone": "Europe/Paris"}
    assert parse_datetime(value) == datetime(2027, 3, 14, 8, 4, tzinfo=ZoneInfo("Europe/Paris"))


def test_datetime_as_plain_string() -> None:
    assert parse_datetime("2027-03-14T08:04:00+01:00") == datetime.fromisoformat(
        "2027-03-14T08:04:00+01:00"
    )


def test_unreadable_datetime_is_none() -> None:
    assert parse_datetime("tomorrow") is None
    assert parse_datetime(None) is None
    assert parse_datetime({"@type": "QDateTime"}) is None


def test_reservation_without_trip_keeps_its_raw_data() -> None:
    hotel = {
        "@type": "LodgingReservation",
        "reservationNumber": "H1",
        "reservationFor": {"@type": "LodgingBusiness", "name": "Hotel"},
    }
    [reservation] = _extract(hotel).reservations
    assert reservation.type == "LodgingReservation"
    assert reservation.reference == "H1"
    assert reservation.departure is None and reservation.arrival is None
    assert reservation.raw == hotel


def test_raw_is_a_copy_the_caller_cannot_alter_through_the_result() -> None:
    element: dict[str, Any] = {
        "@type": "TrainReservation",
        "reservationFor": {"@type": "TrainTrip"},
    }
    original = copy.deepcopy(element)
    [reservation] = _extract(element).reservations
    element["reservationFor"]["trainNumber"] = "changed"
    assert reservation.raw == original


def test_elements_that_are_not_reservations_are_ignored() -> None:
    ticket_only = {"@type": "Ticket", "ticketNumber": "X"}
    result = _extract(ticket_only)
    assert result.reservations == ()
    assert result.nothing_recognised


def test_document_metadata() -> None:
    result = _extract()
    assert result.document is not None
    assert result.document.name == "no-reservation.pdf"
    assert result.document.mime_type == "application/pdf"
    assert len(result.document.id) == 64
