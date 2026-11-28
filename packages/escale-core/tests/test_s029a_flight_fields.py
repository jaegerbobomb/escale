"""S029a — the flight editor's fields, rules and writing (core)."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

import pytest

from escale_core.flight_edit import FlightFields, edited, fields_of, problems
from escale_core.importer import reservation_from_jsonld

FLIGHT: dict[str, Any] = {
    "@type": "FlightReservation",
    "reservationNumber": "ESC-F718",
    "reservedTicket": {"@type": "Ticket", "ticketedSeat": {"@type": "Seat", "seatNumber": "23A"}},
    "reservationFor": {
        "@type": "Flight",
        "airline": {"@type": "Airline", "iataCode": "AF", "name": "Air France"},
        "flightNumber": "718",
        "departureAirport": {"@type": "Airport", "iataCode": "CDG"},
        "departureTime": "2026-09-14T10:25:00+02:00",
        "arrivalAirport": {"@type": "Airport", "iataCode": "LHR"},
        "arrivalTime": "2026-09-14T10:45:00+01:00",
    },
}


def flight(raw: dict[str, Any] = FLIGHT) -> Any:
    r = reservation_from_jsonld(raw, ("d",))
    assert r is not None
    return r


def test_fields_read_the_reservation() -> None:
    f = fields_of(flight())
    assert f == FlightFields(
        flight_number="AF 718",
        departure_terminal="",
        departure_gate="",
        boarding_time="",
        departure_date="2026-09-14",
        departure_time="10:25",
        arrival_terminal="",
        arrival_date="2026-09-14",
        arrival_time="10:45",
        seat="23A",
        reference="ESC-F718",
    )


def test_a_valid_flight_has_no_problem() -> None:
    assert problems(fields_of(flight()), flight()) == []


def test_arrival_before_departure_in_utc() -> None:
    """10:20 in London is 11:20 in Paris: before the 10:25 departure."""
    f = replace(fields_of(flight()), arrival_time="09:20")
    assert problems(f, flight()) == ["The arrival must be after the departure."]
    ok = replace(fields_of(flight()), arrival_time="09:30")  # 10:30 Paris time
    assert problems(ok, flight()) == []


@pytest.mark.parametrize(
    ("change", "problem"),
    [
        ({"departure_time": ""}, "The departure time is required."),
        ({"departure_date": "14/09/2026"}, "The departure is not a valid date and time."),
        ({"boarding_time": "10:40"}, "Boarding must be before the departure."),
        ({"boarding_time": "9h50"}, "The boarding time is not valid (HH:MM)."),
        ({"flight_number": "Air France 718"}, "The flight number is not valid (e.g. AF 718)."),
        ({"arrival_date": "2026-13-01"}, "The arrival is not a valid date and time."),
    ],
)
def test_rules(change: dict[str, str], problem: str) -> None:
    f = replace(fields_of(flight()), **change)
    assert problem in problems(f, flight())


def test_saving_writes_the_json_ld_and_keeps_the_rest() -> None:
    f = replace(
        fields_of(flight()),
        flight_number="BA 303",
        departure_terminal="2E",
        departure_gate="K32",
        boarding_time="09:50",
        arrival_time="11:05",
        seat="12C",
    )
    new = edited(flight(), f)
    trip = new.raw["reservationFor"]
    assert trip["airline"] == {"@type": "Airline", "iataCode": "BA", "name": "Air France"}
    assert trip["flightNumber"] == "303"
    assert (trip["departureTerminal"], trip["departureGate"]) == ("2E", "K32")
    assert trip["boardingTime"] == "2026-09-14T09:50:00+02:00"
    assert trip["arrivalTime"] == "2026-09-14T11:05:00+01:00"  # London's offset kept
    assert trip["departureTime"] == FLIGHT["reservationFor"]["departureTime"]
    assert new.raw["reservedTicket"]["ticketedSeat"]["seatNumber"] == "12C"
    assert new.subject_of == ("d",)


def test_an_untouched_flight_is_unchanged() -> None:
    assert edited(flight(), fields_of(flight())).raw == FLIGHT


def test_boarding_before_midnight_is_the_day_before() -> None:
    raw = {
        **FLIGHT,
        "reservationFor": {
            **FLIGHT["reservationFor"],
            "departureTime": "2026-09-14T00:15:00+02:00",
        },
    }
    f = replace(fields_of(flight(raw)), boarding_time="23:40")
    assert problems(f, flight(raw)) == []
    assert (
        edited(flight(raw), f).raw["reservationFor"]["boardingTime"] == "2026-09-13T23:40:00+02:00"
    )


def test_a_cleared_field_is_removed() -> None:
    raw = {**FLIGHT, "reservationFor": {**FLIGHT["reservationFor"], "departureGate": "K30"}}
    f = replace(fields_of(flight(raw)), departure_gate="")
    assert "departureGate" not in edited(flight(raw), f).raw["reservationFor"]


def test_kde_itinerary_seat_is_kept_in_step() -> None:
    raw = {**FLIGHT, "airplaneSeat": "23A"}
    new = edited(flight(raw), replace(fields_of(flight(raw)), seat="1A"))
    assert new.raw["airplaneSeat"] == "1A"
    assert new.raw["reservedTicket"]["ticketedSeat"]["seatNumber"] == "1A"


def test_a_seat_only_in_airplane_seat_is_read() -> None:
    raw = {k: v for k, v in FLIGHT.items() if k != "reservedTicket"} | {"airplaneSeat": "7F"}
    assert fields_of(flight(raw)).seat == "7F"


def test_a_time_zone_object_is_kept() -> None:
    """KItinerary's QDateTime form: {"@type": "QDateTime", "@value": ..., "timezone": ...}."""
    when = {
        "@type": "QDateTime",
        "@value": "2026-09-14T10:45:00+01:00",
        "timezone": "Europe/London",
    }
    raw = {**FLIGHT, "reservationFor": {**FLIGHT["reservationFor"], "arrivalTime": when}}
    new = edited(flight(raw), replace(fields_of(flight(raw)), arrival_time="11:00"))
    assert new.raw["reservationFor"]["arrivalTime"] == {
        **when,
        "@value": "2026-09-14T11:00:00+01:00",
    }
