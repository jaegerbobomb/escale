"""The flight editor (S029a): KDE Itinerary's ``FlightEditor`` fields, in an action
dialog. The airports are shown in the section titles, not edited (S029b)."""

from __future__ import annotations

from typing import Any

from escale_core.extraction import ExtractedReservation
from escale_core.flight_edit import FlightFields, fields_of, problems
from escale_flet.editor import EditorKind


def _code(r: ExtractedReservation, key: str) -> str:
    trip = r.raw.get("reservationFor")
    airport = trip.get(key) if isinstance(trip, dict) else None
    code = airport.get("iataCode") if isinstance(airport, dict) else None
    return f" · {code}" if isinstance(code, str) and code else ""


def flight_kind(r: ExtractedReservation) -> EditorKind[FlightFields]:
    """The editor for ``r``: its airports name the departure and arrival sections."""
    groups: Any = (
        ("Flight", (("flight_number", "Flight number", "AF 718"),)),
        (
            "Departure" + _code(r, "departureAirport"),
            (
                ("departure_date", "Date", "YYYY-MM-DD"),
                ("departure_time", "Time", "HH:MM"),
                ("boarding_time", "Boarding time", "HH:MM"),
                ("departure_terminal", "Terminal", ""),
                ("departure_gate", "Gate", ""),
            ),
        ),
        (
            "Arrival" + _code(r, "arrivalAirport"),
            (
                ("arrival_date", "Date", "YYYY-MM-DD"),
                ("arrival_time", "Time", "HH:MM"),
                ("arrival_terminal", "Terminal", ""),
            ),
        ),
        ("Booking", (("seat", "Seat", ""), ("reference", "Booking reference", ""))),
    )
    return EditorKind("Edit Flight", groups, fields_of, problems)
