"""S030 — editing a coach or ferry trip: the fields of KDE Itinerary's bus and boat
editors, their validation, and how they are written back."""

from __future__ import annotations

import time
from collections.abc import Iterator
from dataclasses import replace
from typing import Any

import pytest

from escale_core.importer import reservation_from_jsonld
from escale_core.transit_edit import (
    boat_fields,
    bus_fields,
    edited,
    new_boat,
    new_bus,
    problems,
)


@pytest.fixture(autouse=True)
def paris(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TZ", "Europe/Paris")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


BUS: dict[str, Any] = {
    "@type": "BusReservation",
    "reservationNumber": "FLX42",
    "underName": {"@type": "Person", "name": "Ada Lovelace"},
    "reservedTicket": {"@type": "Ticket", "ticketedSeat": {"@type": "Seat", "seatNumber": "12"}},
    "reservationFor": {
        "@type": "BusTrip",
        "busName": "FlixBus",
        "busNumber": "N705",
        "departurePlatform": "B4",
        "departureTime": "2027-07-08T08:00:00+02:00",
        "arrivalTime": "2027-07-08T13:00:00+02:00",
        "departureBusStop": {
            "@type": "BusStation",
            "name": "Paris Bercy",
            "address": {
                "@type": "PostalAddress",
                "streetAddress": "48 bis quai de Bercy",
                "addressLocality": "Paris",
                "addressCountry": "FR",
            },
            "geo": {"@type": "GeoCoordinates", "latitude": 48.835, "longitude": 2.38},
        },
        "arrivalBusStop": {"@type": "BusStation", "name": "Lyon Perrache"},
    },
}


def bus() -> Any:
    r = reservation_from_jsonld(BUS, ("doc",))
    assert r is not None
    return r


def test_the_bus_fields_are_read_from_the_booking() -> None:
    f = bus_fields(bus())
    assert f.bus_number == "FlixBus N705"
    assert (f.departure_name, f.departure_platform) == ("Paris Bercy", "B4")
    assert (f.departure_date, f.departure_time) == ("2027-07-08", "08:00")
    assert (f.departure_street, f.departure_city, f.departure_country) == (
        "48 bis quai de Bercy",
        "Paris",
        "FR",
    )
    assert (f.departure_latitude, f.departure_longitude) == ("48.835", "2.38")
    assert (f.arrival_name, f.arrival_time, f.arrival_city) == ("Lyon Perrache", "13:00", "")
    assert (f.seat, f.reference, f.under_name) == ("12", "FLX42", "Ada Lovelace")
    assert problems(f, bus()) == []


def test_a_new_bus_needs_both_stops_and_a_departure() -> None:
    blank = new_bus()
    assert blank.type == "BusReservation" and blank.subject_of == ()
    assert problems(bus_fields(blank), blank) == [
        "The departure stop is required.",
        "The arrival stop is required.",
        "The departure time is required.",
    ]


def test_a_ferry_names_terminals() -> None:
    blank = new_boat()
    assert blank.type == "BoatReservation"
    assert problems(boat_fields(blank), blank)[:2] == [
        "The departure terminal is required.",
        "The arrival terminal is required.",
    ]


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"departure_time": "8h"}, "The departure is not a valid date and time."),
        ({"arrival_time": "07:00"}, "The arrival must be after the departure."),
        ({"arrival_date": "2027-13-01"}, "The arrival is not a valid date and time."),
        ({"departure_latitude": "north"}, "The departure coordinates are not valid."),
        (
            {"arrival_longitude": "200", "arrival_latitude": "1"},
            "The arrival coordinates are not valid.",
        ),
    ],
)
def test_what_cannot_be_saved(change: dict[str, str], problem: str) -> None:
    f = replace(bus_fields(bus()), **change)
    assert problems(f, bus()) == [problem]


def test_the_arrival_is_optional() -> None:
    f = replace(bus_fields(bus()), arrival_date="", arrival_time="")
    assert problems(f, bus()) == []


def test_editing_writes_kde_s_json_ld_and_keeps_the_rest() -> None:
    f = replace(
        bus_fields(bus()),
        bus_number="N706",
        departure_time="08:15",
        departure_platform="",
        arrival_city="Lyon",
        arrival_latitude="45.749",
        arrival_longitude="4.826",
        seat="14",
        under_name="Ada Lovelace, Bob",
    )
    new = edited(bus(), f)
    trip = new.raw["reservationFor"]
    assert "busName" not in trip and trip["busNumber"] == "N706"  # as KDE writes it
    assert trip["departureTime"] == "2027-07-08T08:15:00+02:00"
    assert "departurePlatform" not in trip
    assert trip["arrivalBusStop"]["address"]["addressLocality"] == "Lyon"
    assert trip["arrivalBusStop"]["geo"]["latitude"] == 45.749
    assert trip["departureBusStop"] == BUS["reservationFor"]["departureBusStop"]
    assert new.raw["reservedTicket"]["ticketedSeat"]["seatNumber"] == "14"
    assert [p["name"] for p in new.raw["underName"]] == ["Ada Lovelace", "Bob"]
    assert new.departure is not None and new.departure.name == "Paris Bercy"
    assert new.subject_of == ("doc",) and new.reference == "FLX42"


def test_an_untouched_booking_is_unchanged() -> None:
    assert edited(bus(), bus_fields(bus())).raw == bus().raw


def test_a_new_ferry_is_written_as_a_boat_trip() -> None:
    blank = new_boat()
    f = replace(
        boat_fields(blank),
        departure_name="Calais",
        departure_date="2027-07-08",
        departure_time="10:00",
        arrival_name="Dover",
        arrival_date="2027-07-08",
        arrival_time="10:30",
        arrival_country="GB",
    )
    assert problems(f, blank) == []
    new = edited(blank, f)
    trip = new.raw["reservationFor"]
    assert trip["@type"] == "BoatTrip"
    assert trip["departureBoatTerminal"] == {"@type": "BoatTerminal", "name": "Calais"}
    assert trip["arrivalBoatTerminal"]["address"]["addressCountry"] == "GB"
    assert trip["departureTime"] == "2027-07-08T10:00:00+02:00"
    assert "reservedTicket" not in new.raw
    assert new.arrival is not None and new.arrival.name == "Dover"
