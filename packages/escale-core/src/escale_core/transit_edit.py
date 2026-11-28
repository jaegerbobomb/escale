"""Editing a coach or ferry trip (S030): the fields of KDE Itinerary's ``BusEditor.qml``
and ``BoatEditor.qml`` in manual mode, each stop with its address
(``FormPlaceEditorDelegate.qml``).

Times are entered in the stop's local time and keep the offset or time zone the
reservation had; a trip added by hand takes the device's offset (S018).
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from escale_core.editing import (
    PLACE_FIELDS,
    coordinates,
    local_moment,
    names,
    place_fields,
    put_names,
    put_text,
    with_moment,
    write_place,
)
from escale_core.extraction import ExtractedReservation
from escale_core.importer import parse_datetime, reservation_from_jsonld


@dataclass(frozen=True)
class BoatFields:
    """What the ferry editor shows, as text; each stop's fields start with its end."""

    departure_name: str = ""
    departure_date: str = ""
    """``YYYY-MM-DD``, at the departure."""
    departure_time: str = ""
    """``HH:MM``."""
    departure_street: str = ""
    departure_postal_code: str = ""
    departure_city: str = ""
    departure_region: str = ""
    departure_country: str = ""
    departure_latitude: str = ""
    departure_longitude: str = ""
    arrival_name: str = ""
    arrival_date: str = ""
    arrival_time: str = ""
    arrival_street: str = ""
    arrival_postal_code: str = ""
    arrival_city: str = ""
    arrival_region: str = ""
    arrival_country: str = ""
    arrival_latitude: str = ""
    arrival_longitude: str = ""
    reference: str = ""
    under_name: str = ""


@dataclass(frozen=True)
class BusFields(BoatFields):
    """The ferry's fields, plus the bus number, the platforms and the seat."""

    bus_number: str = ""
    departure_platform: str = ""
    arrival_platform: str = ""
    seat: str = ""


@dataclass(frozen=True)
class _Mode:
    trip: str
    place: str
    stops: tuple[str, str]
    word: str
    """What a stop is called in the editor's messages."""


_MODES = {
    "BusReservation": _Mode(
        "BusTrip", "BusStation", ("departureBusStop", "arrivalBusStop"), "stop"
    ),
    "BoatReservation": _Mode(
        "BoatTrip", "BoatTerminal", ("departureBoatTerminal", "arrivalBoatTerminal"), "terminal"
    ),
}
_ENDS = (("departure", "departureTime"), ("arrival", "arrivalTime"))


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _new(kind: str) -> ExtractedReservation:
    blank = reservation_from_jsonld(
        {"@type": kind, "reservationFor": {"@type": _MODES[kind].trip}}, ()
    )
    assert blank is not None
    return blank


def new_bus() -> ExtractedReservation:
    """A blank coach trip for the editor to fill: added by hand, it has no document."""
    return _new("BusReservation")


def new_boat() -> ExtractedReservation:
    """A blank ferry crossing for the editor to fill."""
    return _new("BoatReservation")


def _common(r: ExtractedReservation) -> dict[str, str]:
    mode = _MODES[r.type]
    trip = _m(r.raw.get("reservationFor"))
    found = {"reference": r.reference or "", "under_name": names(r.raw.get("underName"))}
    for (end, time_key), stop_key in zip(_ENDS, mode.stops, strict=True):
        stop, moment = _m(trip.get(stop_key)), parse_datetime(trip.get(time_key))
        found[f"{end}_name"] = _text(stop.get("name"))
        found[f"{end}_date"] = f"{moment:%Y-%m-%d}" if moment else ""
        found[f"{end}_time"] = f"{moment:%H:%M}" if moment else ""
        found |= place_fields(stop, f"{end}_")
    return found


def boat_fields(r: ExtractedReservation) -> BoatFields:
    return BoatFields(**_common(r))


def bus_fields(r: ExtractedReservation) -> BusFields:
    trip = _m(r.raw.get("reservationFor"))
    ticket = _m(r.raw.get("reservedTicket"))
    return BusFields(
        **_common(r),
        bus_number=" ".join(
            p for p in (_text(trip.get("busName")), _text(trip.get("busNumber"))) if p
        ),
        departure_platform=_text(trip.get("departurePlatform")),
        arrival_platform=_text(trip.get("arrivalPlatform")),
        seat=_text(_m(ticket.get("ticketedSeat")).get("seatNumber")),
    )


def _moments(f: BoatFields, trip: Mapping[str, Any]) -> tuple[datetime | None, datetime | None]:
    leave = local_moment(f.departure_date, f.departure_time, trip.get("departureTime"))
    original = trip.get("arrivalTime") or trip.get("departureTime")
    return leave, local_moment(f.arrival_date, f.arrival_time, original)


def problems(f: BoatFields, r: ExtractedReservation) -> list[str]:
    """Why the trip cannot be saved, as in KDE Itinerary; empty when it can."""
    word = _MODES[r.type].word
    trip = _m(r.raw.get("reservationFor"))
    leave, reach = _moments(f, trip)
    found = [
        f"The {end} {word} is required."
        for end, _ in _ENDS
        if not getattr(f, f"{end}_name").strip()
    ]
    if not f.departure_date.strip() or not f.departure_time.strip():
        found.append("The departure time is required.")
    elif leave is None:
        found.append("The departure is not a valid date and time.")
    if f.arrival_date.strip() or f.arrival_time.strip():
        if reach is None:
            found.append("The arrival is not a valid date and time.")
        elif leave is not None and reach <= leave:
            found.append("The arrival must be after the departure.")
    for end, _ in _ENDS:
        if coordinates(getattr(f, f"{end}_latitude"), getattr(f, f"{end}_longitude")) is False:
            found.append(f"The {end} coordinates are not valid.")
    return found


def edited(r: ExtractedReservation, f: BoatFields) -> ExtractedReservation:
    """``r`` with the editor's fields written into its JSON-LD; untouched fields stay as
    they were. Call only when ``problems(f, r)`` is empty."""
    mode = _MODES[r.type]
    before = bus_fields(r) if isinstance(f, BusFields) else boat_fields(r)
    values = vars(f)
    changed = {k for k, v in values.items() if v != getattr(before, k)}
    raw = copy.deepcopy(dict(r.raw))
    trip = dict(_m(raw.get("reservationFor"))) or {"@type": mode.trip}
    leave, reach = _moments(f, trip)
    for (end, time_key), stop_key, moment in zip(_ENDS, mode.stops, (leave, reach), strict=True):
        if changed & {f"{end}_date", f"{end}_time"}:
            if moment is not None:
                trip[time_key] = with_moment(moment, trip.get(time_key))
            else:
                trip.pop(time_key, None)  # an arrival left empty
        if changed & {f"{end}_{n}" for n in ("name", *PLACE_FIELDS)}:
            stop = dict(_m(trip.get(stop_key))) or {"@type": mode.place}
            if f"{end}_name" in changed:
                put_text(stop, "name", values[f"{end}_name"])
            write_place(stop, values, changed, f"{end}_")
            trip[stop_key] = stop
    if isinstance(f, BusFields):
        if "bus_number" in changed:  # as KDE writes it
            trip.pop("busName", None)
            put_text(trip, "busNumber", f.bus_number)
        for end in ("departure", "arrival"):
            if f"{end}_platform" in changed:
                put_text(trip, f"{end}Platform", values[f"{end}_platform"])
        if "seat" in changed:
            ticket = dict(_m(raw.get("reservedTicket"))) or {"@type": "Ticket"}
            seat = dict(_m(ticket.get("ticketedSeat"))) or {"@type": "Seat"}
            put_text(seat, "seatNumber", f.seat)
            ticket["ticketedSeat"] = seat
            raw["reservedTicket"] = ticket
    raw["reservationFor"] = trip
    if "reference" in changed:
        put_text(raw, "reservationNumber", f.reference)
    if "under_name" in changed:
        put_names(raw, f.under_name)
    new = reservation_from_jsonld(raw, r.subject_of)
    assert new is not None
    return new
