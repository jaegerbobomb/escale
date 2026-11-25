"""A flight's callsign and a link to follow it live (S016).

Flightradar24 names a flight by its callsign: the airline's ICAO designator and the
flight number (``AF 718`` -> ``AFR718``). Tickets give the IATA code, so the ICAO one
comes from a table built from Wikidata (``tools/airlines_from_wikidata.py``, CC0).
When the airline is not in the table, there is no callsign: no link rather than a
wrong one.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Mapping
from functools import cache
from importlib import resources
from typing import Any

from escale_core.extraction import ExtractedReservation

FLIGHTRADAR24 = "https://www.flightradar24.com/"
_NUMBER = re.compile(r"0*([1-9][0-9]{0,3}[A-Z]?)")


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


@cache
def _airlines() -> dict[str, str]:
    text = resources.files("escale_core").joinpath("data/airlines.csv").read_text()
    rows = csv.DictReader(line for line in text.splitlines() if not line.startswith("#"))
    return {row["iata"]: row["icao"] for row in rows}


def airline_icao(iata: str) -> str | None:
    """The ICAO designator of the airline with this IATA code, when known for sure."""
    return _airlines().get(iata.strip().upper())


def callsign(reservation: ExtractedReservation) -> str | None:
    """``AFR718`` for flight AF 718; ``None`` when unsure."""
    if reservation.type != "FlightReservation":
        return None
    flight = _m(reservation.raw.get("reservationFor"))
    iata = _m(flight.get("airline")).get("iataCode")
    number = flight.get("flightNumber")
    if not isinstance(iata, str) or not isinstance(number, str):
        return None
    icao = airline_icao(iata)
    number = number.strip().upper().replace(" ", "")
    number = number.removeprefix(iata.strip().upper())
    match = _NUMBER.fullmatch(number)
    if icao is None or match is None:
        return None
    return icao + match.group(1)


def follow_link(reservation: ExtractedReservation) -> str | None:
    """A Flightradar24 link that follows the flight while it is in the air."""
    sign = callsign(reservation)
    return FLIGHTRADAR24 + sign if sign else None
