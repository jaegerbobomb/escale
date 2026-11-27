"""Reservations as calendar events, in KDE Itinerary's format (S007, ADR-0004).

One reservation batch is one ``VEVENT``: the batch as a compact JSON array of schema.org
JSON-LD in ``X-KDE-KITINERARY-RESERVATION``, a ``KIT-`` prefixed ``UID``, and what any
calendar shows (``SUMMARY``, ``DTSTART``/``DTEND``, ``LOCATION``), as KItinerary's
``CalendarHandler`` writes them. Escale adds ``X-ESCALE-TRIP`` and ``X-ESCALE-STATE``
when they are set (SPEC § Calendar events). Each reservation names its documents in
``subjectOf`` (S009a). Reading accepts KItinerary's events and Escale's; an event without
the property is not a reservation.
"""

from __future__ import annotations

import json
import re
import uuid
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import icalendar

from escale_core.documents import jsonld, split
from escale_core.extraction import ExtractedReservation
from escale_core.importer import parse_datetime, reservation_from_jsonld
from escale_core.stays import address
from escale_core.trips import span

PAYLOAD = "X-KDE-KITINERARY-RESERVATION"
TRIP = "X-ESCALE-TRIP"
STATE = "X-ESCALE-STATE"
_PRODID = "-//Escale//Escale//EN"


@dataclass(frozen=True)
class CalendarEntry:
    """One calendar event: a batch of reservations and what Escale adds to it."""

    uid: str
    reservations: tuple[ExtractedReservation, ...]
    trip: str | None = None
    """Trip id and name, when the user named or forced the grouping."""
    state: str | None = None
    """``planned`` for a segment added from a search; ``None`` once confirmed."""


def new_entry(
    reservations: Sequence[ExtractedReservation],
    uid: str | None = None,
    trip: str | None = None,
    state: str | None = None,
) -> CalendarEntry:
    """An entry for ``reservations``, with a new ``KIT-`` uid unless one is given."""
    return CalendarEntry(uid or f"KIT-{uuid.uuid4()}", tuple(reservations), trip, state)


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _name(value: object) -> str | None:
    name = _m(value).get("name")
    return name.strip() if isinstance(name, str) and name.strip() else None


def _words(*parts: object) -> str:
    return " ".join(str(p).strip() for p in parts if p and str(p).strip())


def summary(r: ExtractedReservation) -> str:
    """The event's title, as KItinerary words it."""
    target = _m(r.raw.get("reservationFor"))
    dep = r.departure.code or r.departure.name if r.departure else None
    arr = r.arrival.code or r.arrival.name if r.arrival else None
    ends = _words("from", dep) if dep else ""
    ends = _words(ends, "to", arr) if arr else ends
    if r.type == "TrainReservation":
        return _words("Train", target.get("trainNumber"), ends)
    if r.type == "BusReservation":
        return _words("Bus", target.get("busNumber"), ends)
    if r.type == "BoatReservation":
        return _words("Ferry", ends)
    if r.type == "FlightReservation":
        airline = _m(target.get("airline")).get("iataCode")
        return _words("Flight", airline, target.get("flightNumber"), ends)
    if r.type == "LodgingReservation":
        return _words("Hotel reservation:", _name(target))
    if r.type == "FoodEstablishmentReservation":
        return _words("Restaurant reservation:", _name(target))
    if r.type == "RentalCarReservation":
        return _words("Rental car reservation:", _name(target))
    return _name(target) or r.type.removesuffix("Reservation")


def _location(r: ExtractedReservation) -> str | None:
    if r.departure is not None:
        return r.departure.name
    if r.type in ("LodgingReservation", "FoodEstablishmentReservation"):
        return address(r)
    return _name(_m(r.raw.get("reservationFor")).get("location"))


def _moment(value: datetime) -> datetime:
    """A named zone is kept (``TZID``); a bare offset is written in UTC."""
    if isinstance(value.tzinfo, ZoneInfo) or value.tzinfo is None:
        return value
    return value.astimezone(UTC)


def to_event(entry: CalendarEntry) -> icalendar.Event:
    """The ``VEVENT`` for ``entry``; ``ValueError`` when its first reservation has no time."""
    first = entry.reservations[0]
    timing = span(first)
    if timing is None:
        raise ValueError(f"{first.type} without a date: no calendar event")
    event = icalendar.Event()
    event.add("UID", entry.uid)
    event.add("DTSTAMP", datetime.now(UTC))
    event.add("SUMMARY", summary(first))
    start, end = timing
    if first.type == "LodgingReservation":
        checkout = parse_datetime(first.raw.get("checkoutTime"))
        last = checkout.date() if checkout else start.date()
        event.add("DTSTART", start.date())
        event.add("DTEND", max(last, start.date() + timedelta(days=1)))
        event.add("TRANSP", "TRANSPARENT")
    else:
        event.add("DTSTART", _moment(start))
        if end > start:
            event.add("DTEND", _moment(end))
    location = _location(first)
    if location:
        event.add("LOCATION", location)
    payload = [jsonld(r) for r in entry.reservations]
    compact = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    event.add(PAYLOAD, icalendar.vText(compact))  # escaped as TEXT, as libical writes it
    if entry.trip:
        event.add(TRIP, icalendar.vText(entry.trip))
    if entry.state:
        event.add(STATE, icalendar.vText(entry.state))
    return event


def to_ics(entries: Iterable[CalendarEntry]) -> bytes:
    """A ``VCALENDAR`` holding ``entries``, with the time zones they use."""
    calendar = icalendar.Calendar()
    calendar.add("PRODID", _PRODID)
    calendar.add("VERSION", "2.0")
    years: list[int] = []
    for entry in entries:
        event = to_event(entry)
        years.append(event.decoded("DTSTART").year)
        calendar.add_component(event)
    if years:  # transitions around the trips only, not 1970 to 2038
        calendar.add_missing_timezones(date(min(years) - 1, 1, 1), date(max(years) + 2, 1, 1))
    return bytes(calendar.to_ical())


_ESCAPED = re.compile(r"\\([\\;,nN])")


def _serialised(value: object) -> str:
    """A property's value as written in the file: parsed ``X-`` properties are kept
    raw by ``icalendar``, those built in memory are escaped when serialised."""
    to_ical = getattr(value, "to_ical", None)
    written = to_ical() if callable(to_ical) else value
    return written.decode() if isinstance(written, bytes) else str(written)


def _unescape(text: str) -> str:
    r"""RFC 5545 TEXT: ``\,`` ``\;`` ``\\`` ``\n``."""
    return _ESCAPED.sub(lambda m: "\n" if m[1] in "nN" else m[1], text)


def _payload(value: str) -> object:
    """The JSON, written raw (as in some of KItinerary's test data) or escaped as TEXT
    (as libical writes it); ``None`` if it is neither."""
    for text in (value, _unescape(value)):
        try:
            return json.loads(text, strict=False)
        except ValueError:
            continue
    return None


def from_event(event: icalendar.Component) -> CalendarEntry | None:
    """The reservations an event holds; ``None`` when it holds none."""
    raw = event.get(PAYLOAD)
    if raw is None:
        return None
    payload = _payload(_serialised(raw))
    elements = payload if isinstance(payload, list) else [payload]
    found = [reservation_from_jsonld(*split(e)) for e in elements if isinstance(e, Mapping)]
    reservations = tuple(r for r in found if r is not None)
    if not reservations:
        return None
    trip, state = event.get(TRIP), event.get(STATE)
    return CalendarEntry(
        uid=str(event.get("UID", "")),
        reservations=reservations,
        trip=_unescape(_serialised(trip)) if trip is not None else None,
        state=_unescape(_serialised(state)) if state is not None else None,
    )


def entries_in(ics: bytes | str) -> list[CalendarEntry]:
    """Every reservation event of a calendar file; other events are left out."""
    calendar = icalendar.Calendar.from_ical(ics)
    found = (from_event(e) for e in calendar.walk("VEVENT"))
    return [e for e in found if e is not None]
