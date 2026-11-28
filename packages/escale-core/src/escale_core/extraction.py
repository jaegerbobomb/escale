"""What an import extracts from a file, before it becomes a reservation of a trip."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Document:
    """The imported file. ``id`` is the SHA-256 of its content (ADR-0004)."""

    id: str
    name: str
    mime_type: str


@dataclass(frozen=True)
class Stop:
    """One end of a trip: a station, an airport, a bus stop."""

    name: str | None
    time: datetime | None
    code: str | None = None
    """IATA code of an airport; other identifiers are left in the raw JSON-LD."""


@dataclass(frozen=True)
class ExtractedReservation:
    type: str
    """schema.org type, e.g. ``TrainReservation``."""
    raw: Mapping[str, Any]
    """The JSON-LD element as kitinerary printed it, unchanged."""
    reference: str | None
    departure: Stop | None
    arrival: Stop | None
    subject_of: tuple[str, ...]
    """Ids of the documents this reservation comes from (schema.org ``subjectOf``)."""


@dataclass(frozen=True)
class ExtractionResult:
    document: Document | None
    reservations: tuple[ExtractedReservation, ...] = ()
    error: str | None = None
    """Why the file could not be read; ``None`` when extraction ran."""
    source: Path | None = None
    """The file that was read, so that a store can keep a copy of it."""
    documents: tuple[tuple[Document, bytes], ...] = ()
    """Documents read with the reservations, and their content: those of a KDE Itinerary
    export (S028), where ``document`` is ``None``."""
    not_imported: tuple[str, ...] = ()
    """What the file holds that Escale leaves out, in words ("2 passes")."""

    @property
    def nothing_recognised(self) -> bool:
        """Extraction ran and found no reservation in the file."""
        return self.error is None and not self.reservations
