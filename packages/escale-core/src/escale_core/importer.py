"""Import service: a file in, extracted reservations out, never silently (ADR-0003)."""

from __future__ import annotations

import copy
import hashlib
import mimetypes
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from escale_core.adapters.kitinerary_cli import ExtractorError, ExtractorNotFoundError
from escale_core.extraction import Document, ExtractedReservation, ExtractionResult, Stop
from escale_core.store import ReservationStore


class Extractor(Protocol):
    async def extract(self, path: Path) -> list[dict[str, Any]]: ...


# (departure key, arrival key) of each schema.org trip type.
_ENDS: dict[str, tuple[str, str]] = {
    "TrainTrip": ("departureStation", "arrivalStation"),
    "BusTrip": ("departureBusStop", "arrivalBusStop"),
    "Flight": ("departureAirport", "arrivalAirport"),
    "BoatTrip": ("departureBoatTerminal", "arrivalBoatTerminal"),
}


def parse_datetime(value: object) -> datetime | None:
    """A schema.org date-time, as a string or as kitinerary's ``QDateTime`` object."""
    zone: str | None = None
    if isinstance(value, Mapping):
        zone = value.get("timezone")
        value = value.get("@value")
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if isinstance(zone, str):
        try:
            tz = ZoneInfo(zone)
        except (ZoneInfoNotFoundError, ValueError):
            return parsed
        return parsed.astimezone(tz) if parsed.tzinfo else parsed.replace(tzinfo=tz)
    return parsed


def _text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _stop(trip: Mapping[str, Any], place_key: str, time_key: str) -> Stop | None:
    place = trip.get(place_key)
    time = parse_datetime(trip.get(time_key))
    if not isinstance(place, Mapping) and time is None:
        return None
    place = place if isinstance(place, Mapping) else {}
    return Stop(name=_text(place.get("name")), time=time, code=_text(place.get("iataCode")))


def reservation_from_jsonld(
    element: Mapping[str, Any], subject_of: tuple[str, ...]
) -> ExtractedReservation | None:
    """An extracted reservation from one JSON-LD element; ``None`` if it is not one."""
    kind = element.get("@type")
    if not isinstance(kind, str) or not kind.endswith("Reservation"):
        return None
    trip = element.get("reservationFor")
    departure = arrival = None
    if isinstance(trip, Mapping) and trip.get("@type") in _ENDS:
        dep_key, arr_key = _ENDS[trip["@type"]]
        departure = _stop(trip, dep_key, "departureTime")
        arrival = _stop(trip, arr_key, "arrivalTime")
    return ExtractedReservation(
        type=kind,
        raw=copy.deepcopy(dict(element)),
        reference=_text(element.get("reservationNumber")),
        departure=departure,
        arrival=arrival,
        subject_of=subject_of,
    )


def _document(path: Path) -> Document:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            digest.update(chunk)
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return Document(id=digest.hexdigest(), name=path.name, mime_type=mime_type)


async def extract(path: Path, extractor: Extractor) -> ExtractionResult:
    """Extract the reservations of one file. Failures are results, not exceptions."""
    try:
        document = _document(path)
    except OSError as e:
        return ExtractionResult(document=None, error=f"cannot read {path.name}: {e.strerror}")
    try:
        elements = await extractor.extract(path)
    except ExtractorNotFoundError:
        return ExtractionResult(
            document=document, error="The ticket extractor (kitinerary-extractor) is not installed."
        )
    except ExtractorError as e:
        return ExtractionResult(document=document, error=f"The ticket could not be read: {e}")
    reservations = tuple(
        r
        for r in (reservation_from_jsonld(element, (document.id,)) for element in elements)
        if r is not None
    )
    return ExtractionResult(document=document, reservations=reservations, source=path)


class Importer:
    """Import in two steps: ``preview`` reads the file, ``confirm`` saves it (S004).

    Nothing is written before ``confirm``; a result with no reservation saves nothing.
    """

    def __init__(self, extractor: Extractor, store: ReservationStore) -> None:
        self._extractor = extractor
        self._store = store

    async def preview(self, path: Path) -> ExtractionResult:
        return await extract(path, self._extractor)

    async def confirm(self, result: ExtractionResult) -> None:
        if result.document is not None and result.reservations:
            await self._store.add(result.document, result.reservations, result.source)
