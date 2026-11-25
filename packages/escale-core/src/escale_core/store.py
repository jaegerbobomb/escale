"""Where confirmed reservations go.

Nextcloud is the source of truth and SQLite its local cache (ADR-0004); both come with
later stories. Until then the store is this port, with an in-memory implementation.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

from escale_core.extraction import Document, ExtractedReservation


class ReservationStore(Protocol):
    async def add(
        self,
        document: Document,
        reservations: Sequence[ExtractedReservation],
        source: Path | None = None,
    ) -> None:
        """Save ``reservations`` and the document they come from (``source``: its file)."""
        ...

    async def reservations(self) -> tuple[ExtractedReservation, ...]: ...

    async def documents(self) -> tuple[Document, ...]: ...

    async def replace(self, old: ExtractedReservation, new: ExtractedReservation) -> None:
        """Put ``new`` in the place of ``old``, an edited copy of it (S017b)."""
        ...


class InMemoryReservationStore:
    """Keeps everything for the life of the process."""

    def __init__(self) -> None:
        self._reservations: list[ExtractedReservation] = []
        self._documents: dict[str, Document] = {}

    async def add(
        self,
        document: Document,
        reservations: Sequence[ExtractedReservation],
        source: Path | None = None,
    ) -> None:
        self._documents.setdefault(document.id, document)
        self._reservations.extend(reservations)

    async def reservations(self) -> tuple[ExtractedReservation, ...]:
        return tuple(self._reservations)

    async def documents(self) -> tuple[Document, ...]:
        return tuple(self._documents.values())

    async def replace(self, old: ExtractedReservation, new: ExtractedReservation) -> None:
        self._reservations = [new if r == old else r for r in self._reservations]
