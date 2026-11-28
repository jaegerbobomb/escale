"""Editing a flight (S029a): the fields of KDE Itinerary's ``FlightEditor.qml``.

Airports are shown, not edited, as KDE Itinerary does when they have an IATA code;
choosing them comes with the airport table (S029b). Times are entered in each
airport's local time and keep the offset or time zone the reservation had.
"""

from __future__ import annotations

import copy
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from escale_core.editing import local_moment, put_text, with_moment
from escale_core.extraction import ExtractedReservation
from escale_core.importer import parse_datetime, reservation_from_jsonld

FLIGHT_NUMBER = re.compile(r"^\s*([A-Z0-9]{2}[A-Z]?)\s*(\d{1,5})\s*$")
"""As KDE Itinerary checks it: the airline's IATA code, then the number."""
_TIME = re.compile(r"^\s*([01]\d|2[0-3]):([0-5]\d)\s*$")
_DAY = timedelta(days=1)
_BOARDING_WINDOW = timedelta(hours=4)
"""Boarding later than the departure's time of day is the day before only within this."""


@dataclass(frozen=True)
class FlightFields:
    """What the flight editor shows, as text."""

    flight_number: str = ""
    """``AF 718``."""
    departure_terminal: str = ""
    departure_gate: str = ""
    boarding_time: str = ""
    """``HH:MM``, on the departure's day; the day before when that is at most four hours
    before the departure (a flight after midnight)."""
    departure_date: str = ""
    """``YYYY-MM-DD``, at the departure airport."""
    departure_time: str = ""
    arrival_terminal: str = ""
    arrival_date: str = ""
    arrival_time: str = ""
    seat: str = ""
    reference: str = ""


_TEXTS = {
    "departure_terminal": "departureTerminal",
    "departure_gate": "departureGate",
    "arrival_terminal": "arrivalTerminal",
}


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _seat(raw: Mapping[str, Any]) -> str:
    ticketed = _m(_m(raw.get("reservedTicket")).get("ticketedSeat"))
    return _text(ticketed.get("seatNumber")) or _text(raw.get("airplaneSeat"))


def fields_of(r: ExtractedReservation) -> FlightFields:
    trip = _m(r.raw.get("reservationFor"))
    airline = _text(_m(trip.get("airline")).get("iataCode"))
    number = _text(trip.get("flightNumber"))
    leave, reach, board = (
        parse_datetime(trip.get(k)) for k in ("departureTime", "arrivalTime", "boardingTime")
    )
    return FlightFields(
        flight_number=" ".join(p for p in (airline, number) if p),
        **{field: _text(trip.get(key)) for field, key in _TEXTS.items()},
        boarding_time=f"{board:%H:%M}" if board else "",
        departure_date=f"{leave:%Y-%m-%d}" if leave else "",
        departure_time=f"{leave:%H:%M}" if leave else "",
        arrival_date=f"{reach:%Y-%m-%d}" if reach else "",
        arrival_time=f"{reach:%H:%M}" if reach else "",
        seat=_seat(r.raw),
        reference=r.reference or "",
    )


def _zone_of(trip: Mapping[str, Any], *keys: str) -> object:
    """The first stored time among ``keys``: its zone is the one to enter times in."""
    return next((trip[k] for k in keys if trip.get(k) is not None), None)


def _times(
    f: FlightFields, trip: Mapping[str, Any]
) -> tuple[datetime | None, datetime | None, datetime | None]:
    """Departure, arrival and boarding, as the fields give them (``None`` when not)."""
    leave = local_moment(f.departure_date, f.departure_time, trip.get("departureTime"))
    reach = local_moment(
        f.arrival_date, f.arrival_time, _zone_of(trip, "arrivalTime", "departureTime")
    )
    board = None
    if leave is not None and _TIME.match(f.boarding_time):
        board = local_moment(
            f"{leave:%Y-%m-%d}", f.boarding_time, _zone_of(trip, "boardingTime", "departureTime")
        )
        # 23:40 for a 00:15 flight boards the day before; 10:40 for 10:25 is a mistake
        if board is not None and board > leave and leave - (board - _DAY) <= _BOARDING_WINDOW:
            board -= _DAY
    return leave, reach, board


def problems(f: FlightFields, r: ExtractedReservation | None = None) -> list[str]:
    """Why the flight cannot be saved, as in KDE Itinerary; empty when it can."""
    trip = _m(r.raw.get("reservationFor")) if r is not None else {}
    leave, reach, board = _times(f, trip)
    found: list[str] = []
    if not f.departure_date.strip() or not f.departure_time.strip():
        found.append("The departure time is required.")
    elif leave is None:
        found.append("The departure is not a valid date and time.")
    if f.boarding_time.strip() and not _TIME.match(f.boarding_time):
        found.append("The boarding time is not valid (HH:MM).")
    elif board is not None and leave is not None and board >= leave:
        found.append("Boarding must be before the departure.")
    if f.arrival_date.strip() or f.arrival_time.strip():
        if reach is None:
            found.append("The arrival is not a valid date and time.")
        elif leave is not None and reach <= leave:
            found.append("The arrival must be after the departure.")
    if f.flight_number.strip() and not FLIGHT_NUMBER.match(f.flight_number.upper()):
        found.append("The flight number is not valid (e.g. AF 718).")
    return found


def edited(r: ExtractedReservation, f: FlightFields) -> ExtractedReservation:
    """``r`` with the editor's fields written into its JSON-LD; untouched fields stay as
    they were. Call only when ``problems(f, r)`` is empty."""
    before = fields_of(r)
    changed = {k for k, v in vars(f).items() if v != getattr(before, k)}
    raw = copy.deepcopy(dict(r.raw))
    trip = dict(_m(raw.get("reservationFor"))) or {"@type": "Flight"}
    if "flight_number" in changed:
        found = FLIGHT_NUMBER.match(f.flight_number.upper())
        if found:
            airline = dict(_m(trip.get("airline"))) or {"@type": "Airline"}
            airline["iataCode"] = found[1]
            trip["airline"], trip["flightNumber"] = airline, found[2]
        elif not f.flight_number.strip():
            trip.pop("flightNumber", None)
    for field, key in _TEXTS.items():
        if field in changed:
            put_text(trip, key, getattr(f, field))
    leave, reach, board = _times(f, trip)
    for fields, key, moment in (
        ({"departure_date", "departure_time"}, "departureTime", leave),
        ({"arrival_date", "arrival_time"}, "arrivalTime", reach),
    ):
        if changed & fields and moment is not None:
            trip[key] = with_moment(moment, trip.get(key))
    if changed & {"boarding_time", "departure_date", "departure_time"} and f.boarding_time.strip():
        if board is not None:
            original = _zone_of(trip, "boardingTime")
            trip["boardingTime"] = with_moment(board, original)
    elif "boarding_time" in changed:
        trip.pop("boardingTime", None)
    raw["reservationFor"] = trip
    if "seat" in changed:
        ticket = dict(_m(raw.get("reservedTicket"))) or {"@type": "Ticket"}
        seat = dict(_m(ticket.get("ticketedSeat"))) or {"@type": "Seat"}
        put_text(seat, "seatNumber", f.seat)
        ticket["ticketedSeat"] = seat
        raw["reservedTicket"] = ticket
        if "airplaneSeat" in raw:  # as KDE Itinerary writes it
            put_text(raw, "airplaneSeat", f.seat)
    if "reference" in changed:
        put_text(raw, "reservationNumber", f.reference)
    new = reservation_from_jsonld(raw, r.subject_of)
    assert new is not None
    return new
