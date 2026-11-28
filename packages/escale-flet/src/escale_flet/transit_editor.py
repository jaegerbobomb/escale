"""The bus and ferry editors (S030): KDE Itinerary's ``BusEditor`` and ``BoatEditor``
fields, in an action dialog. Each stop's address is a list of its own, under the stop."""

from __future__ import annotations

from typing import Any

from escale_core.transit_edit import BoatFields, BusFields, boat_fields, bus_fields, problems
from escale_flet.editor import DATE, TIME, EditorKind

Rows = tuple[tuple[str, str, str], ...]


def _stop(end: str, word: str, platform: bool) -> Rows:
    rows: Rows = (
        (f"{end}_date", "Date", DATE),
        (f"{end}_time", "Time", TIME),
        (f"{end}_name", f"{word} name", ""),
    )
    return (*rows, (f"{end}_platform", "Platform", "")) if platform else rows


def _address(end: str) -> Rows:
    return (
        (f"{end}_street", "Street", ""),
        (f"{end}_postal_code", "Postal code", ""),
        (f"{end}_city", "City", ""),
        (f"{end}_region", "Region", ""),
        (f"{end}_country", "Country", ""),
        (f"{end}_latitude", "Latitude", "45.7494"),
        (f"{end}_longitude", "Longitude", "4.8270"),
    )


def _ends(word: str, platform: bool) -> tuple[tuple[str, Rows], ...]:
    return (
        ("Departure", _stop("departure", word, platform)),
        (f"Departure {word.lower()} address", _address("departure")),
        ("Arrival", _stop("arrival", word, platform)),
        (f"Arrival {word.lower()} address", _address("arrival")),
    )


_BOOKING = (
    "Booking",
    (("reference", "Booking reference", ""), ("under_name", "Under the name of", "")),
)

BUS: EditorKind[BusFields] = EditorKind(
    "Edit Bus",
    (
        ("Bus", (("bus_number", "Bus number", "N705"),)),
        *_ends("Stop", platform=True),
        ("Seat", (("seat", "Seat", ""),)),
        _BOOKING,
    ),
    bus_fields,
    problems,
)
FERRY: EditorKind[BoatFields] = EditorKind(
    "Edit Ferry", (*_ends("Terminal", platform=False), _BOOKING), boat_fields, problems
)

KINDS: dict[str, EditorKind[Any]] = {"BusReservation": BUS, "BoatReservation": FERRY}
