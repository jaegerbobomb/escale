"""Where confirmed reservations go.

Nextcloud is the source of truth and SQLite its local cache (ADR-0004); both come with
later stories. Until then the store is this port, with an in-memory implementation.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from escale_core.extraction import Document, ExtractedReservation


@dataclass(frozen=True)
class Outgoing:
    """A reservation the calendar does not have as it is now (S008a): never sent (no
    ``uid``), or changed since. ``href`` and ``etag`` are those of its event."""

    reservation: ExtractedReservation
    uid: str | None = None
    href: str | None = None
    etag: str | None = None


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
        """Put ``new`` in the place of ``old``, an edited copy of it (S017b); its
        calendar event stays the same."""
        ...

    async def unsent(self) -> tuple[Outgoing, ...]:
        """The outbox: what the calendar does not have as it is now (S008a)."""
        ...

    async def sent(
        self, reservation: ExtractedReservation, uid: str, href: str, etag: str | None
    ) -> None:
        """``reservation``, as it is here, is now the calendar event ``uid`` at ``href``."""
        ...


@dataclass(frozen=True)
class _Mark:
    uid: str
    href: str
    etag: str | None
    raw: Mapping[str, Any]
    """The JSON-LD as sent: the reservation is in the outbox again once it differs."""


class InMemoryReservationStore:
    """Keeps everything for the life of the process."""

    def __init__(self) -> None:
        self._reservations: list[ExtractedReservation] = []
        self._documents: dict[str, Document] = {}
        self._marks: dict[int, _Mark] = {}
        """Position in ``_reservations`` -> its calendar event."""

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

    async def unsent(self) -> tuple[Outgoing, ...]:
        found = []
        for i, r in enumerate(self._reservations):
            mark = self._marks.get(i)
            if mark is None:
                found.append(Outgoing(r))
            elif mark.raw != r.raw:
                found.append(Outgoing(r, mark.uid, mark.href, mark.etag))
        return tuple(found)

    async def sent(
        self, reservation: ExtractedReservation, uid: str, href: str, etag: str | None
    ) -> None:
        for i, r in enumerate(self._reservations):
            if r == reservation:
                self._marks[i] = _Mark(uid, href, etag, dict(reservation.raw))
