"""S016 — the flight's callsign and its Flightradar24 link (core part)."""

from __future__ import annotations

from typing import Any

import pytest

from escale_core.flights import airline_icao, callsign, follow_link
from escale_core.importer import reservation_from_jsonld


def flight(airline: str | None, number: Any) -> Any:
    target: dict[str, Any] = {"@type": "Flight", "flightNumber": number}
    if airline is not None:
        target["airline"] = {"@type": "Airline", "iataCode": airline}
    r = reservation_from_jsonld({"@type": "FlightReservation", "reservationFor": target}, ())
    assert r is not None
    return r


@pytest.mark.parametrize(
    ("iata", "icao"),
    [("AF", "AFR"), ("BA", "BAW"), ("LH", "DLH"), ("KL", "KLM"), ("U2", "EZY")],
)
def test_table_has_the_main_airlines(iata: str, icao: str) -> None:
    assert airline_icao(iata) == icao


@pytest.mark.parametrize(
    ("airline", "number", "expected"),
    [
        ("AF", "718", "AFR718"),
        ("AF", "0718", "AFR718"),
        ("AF", "AF718", "AFR718"),
        ("af", "718", "AFR718"),
        ("BA", "123A", "BAW123A"),
        ("ZZ", "12", None),
        (None, "718", None),
        ("AF", None, None),
        ("AF", "abc", None),
    ],
)
def test_callsign(airline: str | None, number: Any, expected: str | None) -> None:
    assert callsign(flight(airline, number)) == expected


def test_follow_link_is_flightradar24_with_the_callsign() -> None:
    assert follow_link(flight("AF", "718")) == "https://www.flightradar24.com/AFR718"


def test_no_link_for_a_train() -> None:
    r = reservation_from_jsonld(
        {
            "@type": "TrainReservation",
            "reservationFor": {"@type": "TrainTrip", "trainNumber": "718"},
        },
        (),
    )
    assert r is not None
    assert follow_link(r) is None
