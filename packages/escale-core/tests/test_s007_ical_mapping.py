"""S007 — reservations to calendar events, in KDE Itinerary's format, and back."""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import icalendar
import pytest

from escale_core.ical_mapping import (
    CalendarEntry,
    entries_in,
    from_event,
    new_entry,
    to_event,
    to_ics,
)
from escale_core.importer import reservation_from_jsonld

DATA = Path(__file__).parent / "data"

TRAIN: dict[str, Any] = {
    "@type": "TrainReservation",
    "reservationNumber": "ESC-T1",
    "underName": {"@type": "Person", "name": 'Jane Doe; "J", the traveller'},
    "reservationFor": {
        "@type": "TrainTrip",
        "trainNumber": "9014",
        "departureStation": {"@type": "TrainStation", "name": "Paris Nord"},
        "departureTime": {
            "@type": "QDateTime",
            "@value": "2026-07-08T09:01:00+02:00",
            "timezone": "Europe/Paris",
        },
        "arrivalStation": {"@type": "TrainStation", "name": "London St Pancras"},
        "arrivalTime": "2026-07-08T10:30:00+01:00",
    },
}
HOTEL: dict[str, Any] = {
    "@type": "LodgingReservation",
    "reservationNumber": "ESC-H1",
    "checkinTime": "2026-07-08T15:00:00+01:00",
    "checkoutTime": "2026-07-10T11:00:00+01:00",
    "reservationFor": {
        "@type": "LodgingBusiness",
        "name": "The Hoxton, Holborn",
        "address": {
            "@type": "PostalAddress",
            "streetAddress": "199-206 High Holborn",
            "addressLocality": "London",
        },
    },
}


def entry(*elements: dict[str, Any], **kw: Any) -> CalendarEntry:
    found = [reservation_from_jsonld(e, ()) for e in elements]
    return new_entry([r for r in found if r is not None], **kw)


# --- the story's scenarios ---


def test_round_trip_keeps_the_reservation() -> None:
    written = entry(TRAIN)
    [back] = entries_in(to_ics([written]))
    assert [dict(r.raw) for r in back.reservations] == [TRAIN]
    assert back.uid == written.uid


def test_an_event_written_by_kde_itinerary_is_read() -> None:
    [read] = entries_in((DATA / "kitinerary-hotel.ics").read_bytes())
    [stay] = read.reservations
    assert stay.type == "LodgingReservation"
    assert stay.reference == "1234567890"
    assert stay.raw["reservationFor"]["name"] == "Glo Hotel Sello"
    assert read.uid.startswith("KIT-")


def test_a_plain_calendar_event_is_ignored() -> None:
    plain = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:x\r\nSUMMARY:Dentist\r\n"
    plain += "DTSTART:20260708T090000Z\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n"
    assert entries_in(plain) == []


# --- details ---


def test_the_property_holds_a_compact_json_array() -> None:
    event = to_event(entry(TRAIN))
    payload = str(event["X-KDE-KITINERARY-RESERVATION"])
    assert payload == json.dumps([TRAIN], ensure_ascii=False, separators=(",", ":"))


def test_a_train_event_is_readable_by_any_calendar() -> None:
    event = to_event(entry(TRAIN))
    assert str(event["UID"]).startswith("KIT-")
    assert str(event["SUMMARY"]) == "Train 9014 from Paris Nord to London St Pancras"
    assert str(event["LOCATION"]) == "Paris Nord"
    start, end = event.decoded("DTSTART"), event.decoded("DTEND")
    assert start == datetime.fromisoformat("2026-07-08T09:01:00+02:00")
    assert end == datetime.fromisoformat("2026-07-08T10:30:00+01:00")
    assert event["DTSTART"].params["TZID"] == "Europe/Paris"


def test_a_stay_is_an_all_day_event_that_does_not_block_the_days() -> None:
    event = to_event(entry(HOTEL))
    assert str(event["SUMMARY"]) == "Hotel reservation: The Hoxton, Holborn"
    assert str(event["LOCATION"]) == "199-206 High Holborn, London"
    assert event.decoded("DTSTART") == date(2026, 7, 8)
    assert event.decoded("DTEND") == date(2026, 7, 10)
    assert str(event["TRANSP"]) == "TRANSPARENT"


def test_the_calendar_carries_the_time_zones_it_uses() -> None:
    calendar = icalendar.Calendar.from_ical(to_ics([entry(TRAIN)]))
    assert [str(tz["TZID"]) for tz in calendar.walk("VTIMEZONE")] == ["Europe/Paris"]


def test_escale_properties_are_written_and_read_when_set() -> None:
    written = entry(TRAIN, trip="t-42;London in July", state="planned")
    [back] = entries_in(to_ics([written]))
    assert (back.trip, back.state) == ("t-42;London in July", "planned")
    [bare] = entries_in(to_ics([entry(TRAIN)]))
    assert (bare.trip, bare.state) == (None, None)
    assert "X-ESCALE" not in to_ics([entry(TRAIN)]).decode()


def test_kde_itinerary_unescaped_commas_are_read() -> None:
    [read] = entries_in((DATA / "kitinerary-train.ics").read_bytes())
    [train] = read.reservations
    assert train.reference == "XXX007"
    assert train.departure is not None and train.departure.name == "Nîmes Gare"


def test_a_batch_of_several_reservations_is_kept_together() -> None:
    other = {**TRAIN, "underName": {"@type": "Person", "name": "Alex Martin"}}
    [back] = entries_in(to_ics([entry(TRAIN, other)]))
    assert [dict(r.raw) for r in back.reservations] == [TRAIN, other]


def test_an_unreadable_payload_is_ignored() -> None:
    event = to_event(entry(TRAIN))
    event["X-KDE-KITINERARY-RESERVATION"] = icalendar.vText("{not json")
    assert from_event(event) is None


def test_a_payload_without_reservation_is_ignored() -> None:
    event = to_event(entry(TRAIN))
    event["X-KDE-KITINERARY-RESERVATION"] = icalendar.vText('[{"@type":"Event"}]')
    assert from_event(event) is None


def test_the_payload_is_escaped_as_libical_does() -> None:
    written = to_ics([entry(TRAIN)]).decode()
    assert '"@type":"TrainReservation"\\,' in written.replace("\r\n ", "")


def test_an_event_without_a_date_cannot_be_written() -> None:
    undated = {"@type": "FoodEstablishmentReservation", "reservationFor": {"name": "Chez A"}}
    with pytest.raises(ValueError):
        to_event(entry(undated))


def test_a_uid_is_kept_when_rewritten() -> None:
    written = entry(TRAIN)
    again = new_entry(list(written.reservations), uid=written.uid)
    assert str(to_event(again)["UID"]) == written.uid
