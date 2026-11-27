"""Where confirmed reservations go, and what the calendar sync knows of them.

Nextcloud is the source of truth and the store its local cache (ADR-0004): SQLite on a
device (``sqlite_store``), or this module's in-memory store for tests and the demo. Each
reservation remembers the calendar event it belongs to (S008): its uid, its href, its
ETag, and the JSON-LD the calendar last had, so that what changed since is known. Each
document remembers whether it is on the server yet (S009a).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Protocol

from escale_core.documents import jsonld
from escale_core.extraction import Document, ExtractedReservation


def _travellers(raw: Mapping[str, Any]) -> str:
    people = raw.get("underName")
    listed = people if isinstance(people, list) else [people]
    return ",".join(
        sorted(str(p.get("name")) for p in listed if isinstance(p, Mapping) and p.get("name"))
    )


def identity(reservation: ExtractedReservation) -> str:
    """What makes two extracted reservations the same one.

    Type, reference, departure time and travellers when there is a reference or a time
    (one booking for two travellers is two reservations, as in KDE Itinerary); otherwise
    the whole JSON-LD, so that two reservations with neither are never merged.
    """
    when = (
        reservation.departure.time.isoformat()
        if reservation.departure and reservation.departure.time
        else ""
    )
    if reservation.reference or when:
        who = _travellers(reservation.raw)
        return f"{reservation.type}|{reservation.reference or ''}|{when}|{who}"
    canonical = json.dumps(reservation.raw, sort_keys=True, ensure_ascii=False)
    return "raw|" + hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True)
class Outgoing:
    """A calendar event to write (S008a): reservations the calendar does not have as they
    are now. ``uid``, ``href`` and ``etag`` are ``None`` for a new event; ``batch`` is
    every reservation of the event, so that a batch is written back whole."""

    reservation: ExtractedReservation
    uid: str | None = None
    href: str | None = None
    etag: str | None = None
    batch: tuple[ExtractedReservation, ...] = ()


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

    def document_path(self, document_id: str) -> Path | None:
        """The local copy of a document, if there is one."""
        ...

    async def replace(self, old: ExtractedReservation, new: ExtractedReservation) -> None:
        """Put ``new`` in the place of ``old``, an edited copy of it (S017b); its
        calendar event stays the same."""
        ...

    # --- calendar sync (S008) ---

    async def unsent(self) -> tuple[Outgoing, ...]:
        """The outbox: one entry per event the calendar does not have as it is now."""
        ...

    async def sent(
        self, batch: Sequence[ExtractedReservation], uid: str, href: str, etag: str | None
    ) -> None:
        """``batch``, as it is here, is now the calendar event ``uid`` at ``href``."""
        ...

    async def received(
        self,
        uid: str,
        href: str,
        etag: str | None,
        batch: Sequence[ExtractedReservation],
        force: bool = False,
    ) -> bool:
        """The calendar's version of an event replaces the local one; ``False`` (and
        nothing changed) while a local change of that event waits to be sent, unless
        ``force`` (the server's version wins, S008c)."""
        ...

    async def removed(self, href: str, force: bool = False) -> bool:
        """The event at ``href`` is gone from the calendar: its reservations go too;
        ``False`` (and nothing changed) while a local change of it waits to be sent,
        unless ``force``."""
        ...

    async def events(self) -> dict[str, str | None]:
        """The calendar events the store holds reservations of: href -> ETag."""
        ...

    async def calendar_token(self, calendar: str) -> str | None: ...

    async def set_calendar_token(self, calendar: str, token: str | None) -> None: ...

    # --- documents (S009a) ---

    async def unsent_documents(self) -> tuple[tuple[Document, Path], ...]:
        """Documents with a local copy that are not on the server yet, and that copy."""
        ...

    async def document_sent(self, document_id: str) -> None:
        """The document is on the server."""
        ...


@dataclass
class _Row:
    reservation: ExtractedReservation
    uid: str | None = None
    href: str | None = None
    etag: str | None = None
    sent: Mapping[str, Any] | None = None
    """The JSON-LD the calendar has, ``subjectOf`` included; the row waits to be sent
    while it differs."""

    @property
    def pending(self) -> bool:
        return self.sent is None or self.sent != jsonld(self.reservation)


@dataclass
class InMemoryReservationStore:
    """Keeps everything for the life of the process."""

    _rows: dict[str, _Row] = field(default_factory=dict)
    _documents: dict[str, Document] = field(default_factory=dict)
    _tokens: dict[str, str | None] = field(default_factory=dict)
    _files: dict[str, Path] = field(default_factory=dict)
    _uploaded: set[str] = field(default_factory=set)

    async def add(
        self,
        document: Document,
        reservations: Sequence[ExtractedReservation],
        source: Path | None = None,
    ) -> None:
        self._documents.setdefault(document.id, document)
        if source is not None and source.is_file():
            self._files.setdefault(document.id, source)
        for r in reservations:
            key = identity(r)
            row = self._rows.get(key)
            if row is None:
                self._rows[key] = _Row(r)
                continue
            known = row.reservation
            added = tuple(d for d in r.subject_of if d not in known.subject_of)
            if added:
                row.reservation = _with_documents(known, known.subject_of + added)

    async def reservations(self) -> tuple[ExtractedReservation, ...]:
        return tuple(row.reservation for row in self._rows.values())

    async def documents(self) -> tuple[Document, ...]:
        return tuple(self._documents.values())

    def document_path(self, document_id: str) -> Path | None:
        path = self._files.get(document_id)
        return path if path is not None and path.is_file() else None

    async def replace(self, old: ExtractedReservation, new: ExtractedReservation) -> None:
        key = identity(old)
        if key in self._rows:
            self._rows[key].reservation = new
            # same place, so that a batch keeps its order
            self._rows = {(identity(new) if k == key else k): r for k, r in self._rows.items()}

    async def unsent(self) -> tuple[Outgoing, ...]:
        found: list[Outgoing] = []
        seen: set[str] = set()
        for row in self._rows.values():
            if not row.pending or (row.uid is not None and row.uid in seen):
                continue
            if row.uid is None:
                found.append(Outgoing(row.reservation, batch=(row.reservation,)))
                continue
            seen.add(row.uid)
            batch = tuple(r.reservation for r in self._rows.values() if r.uid == row.uid)
            found.append(Outgoing(row.reservation, row.uid, row.href, row.etag, batch))
        return tuple(found)

    async def sent(
        self, batch: Sequence[ExtractedReservation], uid: str, href: str, etag: str | None
    ) -> None:
        for r in batch:
            row = self._rows.get(identity(r))
            if row is not None:
                row.uid, row.href, row.etag, row.sent = uid, href, etag, jsonld(r)

    async def received(
        self,
        uid: str,
        href: str,
        etag: str | None,
        batch: Sequence[ExtractedReservation],
        force: bool = False,
    ) -> bool:
        keys = {identity(r) for r in batch}
        mine = [k for k, row in self._rows.items() if row.href == href or k in keys]
        if not force and any(self._rows[k].pending and self._rows[k].uid for k in mine):
            return False
        documents = {k: self._rows[k].reservation.subject_of for k in mine}
        for k in mine:
            if self._rows[k].href == href:
                del self._rows[k]
        for r in batch:
            key = identity(r)
            kept = documents.get(key, ())
            both = kept + tuple(d for d in r.subject_of if d not in kept)
            self._rows[key] = _Row(_with_documents(r, both), uid, href, etag, jsonld(r))
        return True

    async def removed(self, href: str, force: bool = False) -> bool:
        mine = [k for k, row in self._rows.items() if row.href == href]
        if not force and any(self._rows[k].pending for k in mine):
            return False
        for k in mine:
            del self._rows[k]
        return True

    async def events(self) -> dict[str, str | None]:
        return {row.href: row.etag for row in self._rows.values() if row.href}

    async def calendar_token(self, calendar: str) -> str | None:
        return self._tokens.get(calendar)

    async def set_calendar_token(self, calendar: str, token: str | None) -> None:
        self._tokens[calendar] = token

    async def unsent_documents(self) -> tuple[tuple[Document, Path], ...]:
        found = ((d, self.document_path(d.id)) for d in self._documents.values())
        return tuple((d, p) for d, p in found if p is not None and d.id not in self._uploaded)

    async def document_sent(self, document_id: str) -> None:
        self._uploaded.add(document_id)


def _with_documents(r: ExtractedReservation, subject_of: tuple[str, ...]) -> ExtractedReservation:
    return replace(r, subject_of=subject_of)
