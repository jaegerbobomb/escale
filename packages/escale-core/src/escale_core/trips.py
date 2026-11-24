"""Group reservations into trips and outings (S010a).

A simpler cousin of KDE Itinerary's ``TripGroupManager``: no home location yet, so a trip
closes when the traveller is back where it started, or when nothing follows within a day.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from escale_core.extraction import ExtractedReservation
from escale_core.importer import parse_datetime

TripKind = Literal["trip", "outing"]

GAP = timedelta(days=1)
"""A reservation starting within this time of the trip's end joins it."""

LONGEST_TRIP = timedelta(days=30)
"""A trip waiting for its way back gives up after this long."""

_TRANSPORT = {"TrainReservation", "FlightReservation", "BusReservation", "BoatReservation"}


@dataclass(frozen=True)
class Trip:
    kind: TripKind
    name: str
    start: datetime
    end: datetime
    reservations: tuple[ExtractedReservation, ...]


@dataclass(frozen=True)
class _Timed:
    reservation: ExtractedReservation
    start: datetime
    end: datetime


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def span(reservation: ExtractedReservation) -> tuple[datetime, datetime] | None:
    """When a reservation starts and ends, from its JSON-LD; ``None`` without any time."""
    raw = reservation.raw
    target = _mapping(raw.get("reservationFor"))
    if reservation.departure is not None or reservation.arrival is not None:
        start = reservation.departure.time if reservation.departure else None
        end = reservation.arrival.time if reservation.arrival else None
    elif reservation.type == "LodgingReservation":
        start, end = parse_datetime(raw.get("checkinTime")), parse_datetime(raw.get("checkoutTime"))
    elif reservation.type == "EventReservation":
        start, end = parse_datetime(target.get("startDate")), parse_datetime(target.get("endDate"))
    else:
        start = parse_datetime(raw.get("startTime")) or parse_datetime(target.get("startDate"))
        end = parse_datetime(raw.get("endTime")) or parse_datetime(target.get("endDate"))
    start = start or end
    if start is None:
        return None
    return start, max(end or start, start)


def _town(place: object) -> str | None:
    place = _mapping(place)
    town = _mapping(place.get("address")).get("addressLocality")
    if isinstance(town, str) and town:
        return town
    name = place.get("name")
    return name if isinstance(name, str) and name else None


def _ends(reservation: ExtractedReservation) -> tuple[str | None, str | None]:
    """Town (or place name) a transport leaves from and arrives at."""
    if reservation.type not in _TRANSPORT:
        return None, None
    trip = _mapping(reservation.raw.get("reservationFor"))
    keys = {
        "TrainReservation": ("departureStation", "arrivalStation"),
        "FlightReservation": ("departureAirport", "arrivalAirport"),
        "BusReservation": ("departureBusStop", "arrivalBusStop"),
        "BoatReservation": ("departureBoatTerminal", "arrivalBoatTerminal"),
    }[reservation.type]
    return _town(trip.get(keys[0])), _town(trip.get(keys[1]))


def _is_outing(items: Sequence[_Timed]) -> bool:
    days = {item.start.date() for item in items} | {item.end.date() for item in items}
    kinds = {item.reservation.type for item in items}
    return len(days) == 1 and not kinds & (_TRANSPORT | {"LodgingReservation"})


def _event_name(reservation: ExtractedReservation) -> str | None:
    name = _mapping(reservation.raw.get("reservationFor")).get("name")
    return name if isinstance(name, str) and name else None


def _name(kind: TripKind, items: Sequence[_Timed]) -> str:
    if kind == "outing":
        names = [n for n in (_event_name(i.reservation) for i in items) if n]
        return " + ".join(dict.fromkeys(names)) or "Outing"
    for item in items:
        if item.reservation.type == "LodgingReservation":
            town = _town(item.reservation.raw.get("reservationFor"))
            if town:
                return town
    for item in items:
        _, arrival = _ends(item.reservation)
        if arrival:
            return arrival
    return _event_name(items[0].reservation) or "Trip"


def _trip(items: Sequence[_Timed]) -> Trip:
    kind: TripKind = "outing" if _is_outing(items) else "trip"
    return Trip(
        kind=kind,
        name=_name(kind, items),
        start=items[0].start,
        end=max(item.end for item in items),
        reservations=tuple(item.reservation for item in items),
    )


def group(reservations: Iterable[ExtractedReservation]) -> list[Trip]:
    """Trips and outings, in time order; reservations without any time are left out."""
    timed = sorted(
        (_Timed(r, *s) for r in reservations if (s := span(r)) is not None),
        key=lambda item: (item.start, item.end),
    )
    trips: list[Trip] = []
    current: list[_Timed] = []
    origin: str | None = None
    back_home = False
    for item in timed:
        if current:
            end = max(i.end for i in current)
            waiting = origin is not None and not back_home
            close = item.start - end <= GAP
            within = item.start - current[0].start <= LONGEST_TRIP
            if not (close or (waiting and within)):
                trips.append(_trip(current))
                current, origin, back_home = [], None, False
        if not current:
            origin, _ = _ends(item.reservation)
        current.append(item)
        _, arrival = _ends(item.reservation)
        if origin is not None and arrival == origin and len(current) > 1:
            back_home = True
    if current:
        trips.append(_trip(current))
    return trips


def active_trip(trips: Sequence[Trip], now: datetime) -> Trip | None:
    """The trip in progress at ``now``, else the next one to start."""
    for trip in trips:
        if trip.start <= now <= trip.end:
            return trip
    upcoming = [trip for trip in trips if trip.start > now]
    return min(upcoming, key=lambda trip: trip.start) if upcoming else None
