"""Reservations and documents kept on this device (S014, ADR-0004).

SQLite holds the reservations as kitinerary printed them, plus their document ids; the
files themselves sit next to it as ``documents/<sha256>/<name>`` with a ``meta.json``
(KDE Itinerary's layout). It is a cache of the user's Nextcloud once the sync exists.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sqlite3
import threading
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from escale_core.extraction import Document, ExtractedReservation
from escale_core.importer import reservation_from_jsonld
from escale_core.store import Outgoing

SCHEMA_VERSION = 2

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mime_type TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY,
    identity TEXT NOT NULL UNIQUE,
    raw TEXT NOT NULL,
    subject_of TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS calendar_events (
    identity TEXT PRIMARY KEY,
    uid TEXT NOT NULL,
    href TEXT NOT NULL,
    etag TEXT,
    sent TEXT NOT NULL
);
"""
"""``calendar_events`` (version 2, S008a): the event of each reservation sent to the
calendar, and the JSON-LD it was sent with."""


def default_data_dir() -> Path:
    """``$XDG_DATA_HOME/escale``, or ``~/.local/share/escale``."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "escale"


def identity(reservation: ExtractedReservation) -> str:
    """What makes two extracted reservations the same one.

    Type, reference and departure time when there is a reference or a time; otherwise
    the whole JSON-LD, so that two reservations with neither are never merged.
    """
    when = (
        reservation.departure.time.isoformat()
        if reservation.departure and reservation.departure.time
        else ""
    )
    if reservation.reference or when:
        return f"{reservation.type}|{reservation.reference or ''}|{when}"
    canonical = json.dumps(reservation.raw, sort_keys=True, ensure_ascii=False)
    return "raw|" + hashlib.sha256(canonical.encode()).hexdigest()


class SqliteReservationStore:
    """``ReservationStore`` in ``<data_dir>/escale.sqlite`` and ``<data_dir>/documents/``.

    Nothing is created on disk before the first read or write.
    """

    def __init__(self, data_dir: Path) -> None:
        self._dir = data_dir
        self._db: sqlite3.Connection | None = None
        self._lock = threading.Lock()

    # --- connection ---

    def _connect(self) -> sqlite3.Connection:
        if self._db is None:
            self._dir.mkdir(parents=True, exist_ok=True)
            db = sqlite3.connect(self._dir / "escale.sqlite", check_same_thread=False)
            db.executescript(_SCHEMA)
            db.execute(
                "INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
                (str(SCHEMA_VERSION),),
            )
            db.commit()
            self._db = db
        return self._db

    def close(self) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None

    def schema_version(self) -> int:
        with self._lock:
            row = (
                self._connect()
                .execute("SELECT value FROM meta WHERE key = 'schema_version'")
                .fetchone()
            )
        return int(row[0])

    # --- documents on disk ---

    def document_path(self, document_id: str) -> Path | None:
        """The stored copy of a document, if there is one."""
        folder = self._dir / "documents" / document_id
        meta = folder / "meta.json"
        if not meta.is_file():
            return None
        name = json.loads(meta.read_text(encoding="utf-8")).get("name")
        path = folder / str(name)
        return path if path.is_file() else None

    def _keep_file(self, document: Document, source: Path) -> None:
        folder = self._dir / "documents" / document.id
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / Path(document.name).name
        if not target.exists():
            shutil.copyfile(source, target)
        meta = {
            "@type": "DigitalDocument",
            "name": target.name,
            "encodingFormat": document.mime_type,
        }
        (folder / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # --- ReservationStore ---

    def _add(
        self,
        document: Document,
        reservations: Sequence[ExtractedReservation],
        source: Path | None,
    ) -> None:
        with self._lock:
            db = self._connect()
            if source is not None and source.is_file():
                self._keep_file(document, source)
            with db:
                db.execute(
                    "INSERT OR IGNORE INTO documents (id, name, mime_type) VALUES (?, ?, ?)",
                    (document.id, document.name, document.mime_type),
                )
                for reservation in reservations:
                    key = identity(reservation)
                    row = db.execute(
                        "SELECT subject_of FROM reservations WHERE identity = ?", (key,)
                    ).fetchone()
                    if row is None:
                        db.execute(
                            "INSERT INTO reservations (identity, raw, subject_of) VALUES (?, ?, ?)",
                            (
                                key,
                                json.dumps(dict(reservation.raw)),
                                json.dumps(reservation.subject_of),
                            ),
                        )
                        continue
                    subject_of: list[str] = json.loads(row[0])
                    added = [d for d in reservation.subject_of if d not in subject_of]
                    if added:
                        db.execute(
                            "UPDATE reservations SET subject_of = ? WHERE identity = ?",
                            (json.dumps(subject_of + added), key),
                        )

    def _reservations(self) -> tuple[ExtractedReservation, ...]:
        with self._lock:
            rows = (
                self._connect()
                .execute("SELECT raw, subject_of FROM reservations ORDER BY id")
                .fetchall()
            )
        found: list[ExtractedReservation] = []
        for raw, subject_of in rows:
            element: dict[str, Any] = json.loads(raw)
            reservation = reservation_from_jsonld(element, tuple(json.loads(subject_of)))
            if reservation is not None:
                found.append(reservation)
        return tuple(found)

    def _documents(self) -> tuple[Document, ...]:
        with self._lock:
            rows = (
                self._connect()
                .execute("SELECT id, name, mime_type FROM documents ORDER BY rowid")
                .fetchall()
            )
        return tuple(Document(id=i, name=n, mime_type=m) for i, n, m in rows)

    def _replace(self, old: ExtractedReservation, new: ExtractedReservation) -> None:
        with self._lock:
            db = self._connect()
            with db:
                db.execute(
                    "UPDATE reservations SET identity = ?, raw = ? WHERE identity = ?",
                    (identity(new), json.dumps(dict(new.raw)), identity(old)),
                )
                db.execute(
                    "UPDATE calendar_events SET identity = ? WHERE identity = ?",
                    (identity(new), identity(old)),
                )

    def _unsent(self) -> tuple[Outgoing, ...]:
        with self._lock:
            rows = (
                self._connect()
                .execute(
                    "SELECT r.raw, r.subject_of, e.uid, e.href, e.etag, e.sent"
                    " FROM reservations r LEFT JOIN calendar_events e USING (identity)"
                    " ORDER BY r.id"
                )
                .fetchall()
            )
        found: list[Outgoing] = []
        for raw, subject_of, uid, href, etag, sent in rows:
            element: dict[str, Any] = json.loads(raw)
            if sent is not None and json.loads(sent) == element:
                continue
            reservation = reservation_from_jsonld(element, tuple(json.loads(subject_of)))
            if reservation is not None:
                found.append(Outgoing(reservation, uid, href, etag))
        return tuple(found)

    def _sent(
        self, reservation: ExtractedReservation, uid: str, href: str, etag: str | None
    ) -> None:
        with self._lock:
            db = self._connect()
            with db:
                db.execute(
                    "INSERT OR REPLACE INTO calendar_events (identity, uid, href, etag, sent)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (identity(reservation), uid, href, etag, json.dumps(dict(reservation.raw))),
                )

    async def unsent(self) -> tuple[Outgoing, ...]:
        return await asyncio.to_thread(self._unsent)

    async def sent(
        self, reservation: ExtractedReservation, uid: str, href: str, etag: str | None
    ) -> None:
        await asyncio.to_thread(self._sent, reservation, uid, href, etag)

    async def add(
        self,
        document: Document,
        reservations: Sequence[ExtractedReservation],
        source: Path | None = None,
    ) -> None:
        await asyncio.to_thread(self._add, document, reservations, source)

    async def reservations(self) -> tuple[ExtractedReservation, ...]:
        return await asyncio.to_thread(self._reservations)

    async def documents(self) -> tuple[Document, ...]:
        return await asyncio.to_thread(self._documents)

    async def replace(self, old: ExtractedReservation, new: ExtractedReservation) -> None:
        await asyncio.to_thread(self._replace, old, new)
