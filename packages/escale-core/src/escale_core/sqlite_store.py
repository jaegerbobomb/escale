"""Reservations and documents kept on this device (S014, ADR-0004).

SQLite holds the reservations as kitinerary printed them, plus their document ids; the
files themselves sit next to it as ``documents/<sha256>/<name>`` with a ``meta.json``
(KDE Itinerary's layout). It is a cache of the user's Nextcloud: each reservation
remembers its calendar event and what the calendar last had (S008); each document,
whether it is on the server (S009a).
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sqlite3
import threading
from collections.abc import Sequence
from pathlib import Path

from escale_core.documents import file_name, meta, payload
from escale_core.extraction import Document, ExtractedReservation
from escale_core.importer import reservation_from_jsonld
from escale_core.store import Outgoing, identity

__all__ = ["SCHEMA_VERSION", "SqliteReservationStore", "default_data_dir", "identity"]

SCHEMA_VERSION = 4

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    uploaded INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY,
    identity TEXT NOT NULL UNIQUE,
    raw TEXT NOT NULL,
    subject_of TEXT NOT NULL,
    uid TEXT,
    href TEXT,
    etag TEXT,
    sent TEXT
);
"""
"""Version 3 (S008b): ``uid``, ``href``, ``etag`` and ``sent`` (the JSON-LD the calendar
has) on each reservation; identities include the travellers. Version 4 (S009a):
``uploaded`` on each document, and ``sent`` holds ``subjectOf`` too."""

_SYNC_COLUMNS = ("uid", "href", "etag", "sent")


def default_data_dir() -> Path:
    """``$XDG_DATA_HOME/escale``, or ``~/.local/share/escale``."""
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / "escale"


def _migrate(db: sqlite3.Connection) -> None:
    """Bring a database written by an earlier version up to ``SCHEMA_VERSION``."""
    if "uploaded" not in {row[1] for row in db.execute("PRAGMA table_info(documents)")}:
        db.execute("ALTER TABLE documents ADD COLUMN uploaded INTEGER NOT NULL DEFAULT 0")
    columns = {row[1] for row in db.execute("PRAGMA table_info(reservations)")}
    for column in _SYNC_COLUMNS:
        if column not in columns:
            db.execute(f"ALTER TABLE reservations ADD COLUMN {column} TEXT")
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "calendar_events" in tables:  # version 2 (S008a) kept them apart
        db.execute(
            "UPDATE reservations SET (uid, href, etag, sent) = "
            "(SELECT uid, href, etag, sent FROM calendar_events e"
            " WHERE e.identity = reservations.identity)"
            " WHERE identity IN (SELECT identity FROM calendar_events)"
        )
        db.execute("DROP TABLE calendar_events")
    for row_id, raw, subject_of in db.execute(
        "SELECT id, raw, subject_of FROM reservations"
    ).fetchall():
        reservation = reservation_from_jsonld(json.loads(raw), tuple(json.loads(subject_of)))
        if reservation is not None:
            db.execute(
                "UPDATE OR IGNORE reservations SET identity = ? WHERE id = ?",
                (identity(reservation), row_id),
            )


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
            with db:
                row = db.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
                if row is not None and int(row[0]) < SCHEMA_VERSION:
                    _migrate(db)
                db.execute(
                    "INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
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
        target = folder / file_name(document)
        if not target.exists():
            shutil.copyfile(source, target)
        described = json.dumps(meta(document), indent=2)
        (folder / "meta.json").write_text(described, encoding="utf-8")

    # --- reservations ---

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

    @staticmethod
    def _reservation(raw: str, subject_of: str) -> ExtractedReservation | None:
        return reservation_from_jsonld(json.loads(raw), tuple(json.loads(subject_of)))

    def _reservations(self) -> tuple[ExtractedReservation, ...]:
        with self._lock:
            rows = (
                self._connect()
                .execute("SELECT raw, subject_of FROM reservations ORDER BY id")
                .fetchall()
            )
        found = (self._reservation(raw, subject_of) for raw, subject_of in rows)
        return tuple(r for r in found if r is not None)

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

    # --- calendar sync (S008) ---

    @staticmethod
    def _pending(raw: str, subject_of: str, sent: str | None) -> bool:
        """The calendar does not have the reservation as it is here."""
        return sent is None or json.loads(sent) != payload(json.loads(raw), json.loads(subject_of))

    def _unsent(self) -> tuple[Outgoing, ...]:
        with self._lock:
            db = self._connect()
            rows = [
                (raw, subject_of, uid, href, etag)
                for raw, subject_of, uid, href, etag, sent in db.execute(
                    "SELECT raw, subject_of, uid, href, etag, sent FROM reservations ORDER BY id"
                )
                if self._pending(raw, subject_of, sent)
            ]
            batches = {
                uid: db.execute(
                    "SELECT raw, subject_of FROM reservations WHERE uid = ? ORDER BY id", (uid,)
                ).fetchall()
                for uid in {row[2] for row in rows if row[2] is not None}
            }
        found: list[Outgoing] = []
        seen: set[str] = set()
        for raw, subject_of, uid, href, etag in rows:
            reservation = self._reservation(raw, subject_of)
            if reservation is None or (uid is not None and uid in seen):
                continue
            if uid is None:
                found.append(Outgoing(reservation, batch=(reservation,)))
                continue
            seen.add(uid)
            batch = (self._reservation(r, s) for r, s in batches[uid])
            found.append(Outgoing(reservation, uid, href, etag, tuple(b for b in batch if b)))
        return tuple(found)

    def _sent(
        self, batch: Sequence[ExtractedReservation], uid: str, href: str, etag: str | None
    ) -> None:
        with self._lock:
            db = self._connect()
            with db:
                for r in batch:
                    db.execute(
                        "UPDATE reservations SET uid = ?, href = ?, etag = ?, sent = ?"
                        " WHERE identity = ?",
                        (uid, href, etag, json.dumps(payload(r.raw, r.subject_of)), identity(r)),
                    )

    def _received(
        self,
        uid: str,
        href: str,
        etag: str | None,
        batch: Sequence[ExtractedReservation],
        force: bool,
    ) -> bool:
        keys = [identity(r) for r in batch]
        marks = ",".join("?" * len(keys))
        with self._lock:
            db = self._connect()
            with db:
                mine = db.execute(
                    "SELECT identity, raw, subject_of, uid, sent FROM reservations"
                    f" WHERE href = ? OR identity IN ({marks})",
                    (href, *keys),
                ).fetchall()
                waiting = (u is not None and self._pending(r, s, sent) for _, r, s, u, sent in mine)
                if not force and any(waiting):
                    return False
                documents = {key: json.loads(subject_of) for key, _, subject_of, _, _ in mine}
                db.execute("DELETE FROM reservations WHERE href = ?", (href,))
                for key, r in zip(keys, batch, strict=True):
                    kept: list[str] = documents.get(key, [])
                    both = kept + [d for d in r.subject_of if d not in kept]
                    db.execute(
                        "INSERT OR REPLACE INTO reservations"
                        " (identity, raw, subject_of, uid, href, etag, sent)"
                        " VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            key,
                            json.dumps(dict(r.raw)),
                            json.dumps(both),
                            uid,
                            href,
                            etag,
                            json.dumps(payload(r.raw, r.subject_of)),
                        ),
                    )
        return True

    def _removed(self, href: str, force: bool) -> bool:
        with self._lock:
            db = self._connect()
            with db:
                rows = db.execute(
                    "SELECT raw, subject_of, sent FROM reservations WHERE href = ?", (href,)
                ).fetchall()
                if not force and any(self._pending(*row) for row in rows):
                    return False
                db.execute("DELETE FROM reservations WHERE href = ?", (href,))
        return True

    def _events(self) -> dict[str, str | None]:
        with self._lock:
            rows = (
                self._connect()
                .execute("SELECT DISTINCT href, etag FROM reservations WHERE href IS NOT NULL")
                .fetchall()
            )
        return {href: etag for href, etag in rows}

    def _token(self, calendar: str) -> str | None:
        with self._lock:
            row = (
                self._connect()
                .execute("SELECT value FROM meta WHERE key = ?", (f"token {calendar}",))
                .fetchone()
            )
        return str(row[0]) if row else None

    def _set_token(self, calendar: str, token: str | None) -> None:
        with self._lock:
            db = self._connect()
            with db:
                if token is None:
                    db.execute("DELETE FROM meta WHERE key = ?", (f"token {calendar}",))
                else:
                    db.execute(
                        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)",
                        (f"token {calendar}", token),
                    )

    # --- documents (S009a) ---

    def _unsent_documents(self) -> tuple[tuple[Document, Path], ...]:
        with self._lock:
            rows = (
                self._connect()
                .execute("SELECT id, name, mime_type FROM documents WHERE uploaded = 0")
                .fetchall()
            )
        found = ((Document(i, n, m), self.document_path(i)) for i, n, m in rows)
        return tuple((d, path) for d, path in found if path is not None)

    def _document_sent(self, document_id: str) -> None:
        with self._lock:
            db = self._connect()
            with db:
                db.execute("UPDATE documents SET uploaded = 1 WHERE id = ?", (document_id,))

    # --- ReservationStore ---

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

    async def unsent(self) -> tuple[Outgoing, ...]:
        return await asyncio.to_thread(self._unsent)

    async def sent(
        self, batch: Sequence[ExtractedReservation], uid: str, href: str, etag: str | None
    ) -> None:
        await asyncio.to_thread(self._sent, batch, uid, href, etag)

    async def received(
        self,
        uid: str,
        href: str,
        etag: str | None,
        batch: Sequence[ExtractedReservation],
        force: bool = False,
    ) -> bool:
        return await asyncio.to_thread(self._received, uid, href, etag, batch, force)

    async def removed(self, href: str, force: bool = False) -> bool:
        return await asyncio.to_thread(self._removed, href, force)

    async def events(self) -> dict[str, str | None]:
        return await asyncio.to_thread(self._events)

    async def calendar_token(self, calendar: str) -> str | None:
        return await asyncio.to_thread(self._token, calendar)

    async def set_calendar_token(self, calendar: str, token: str | None) -> None:
        await asyncio.to_thread(self._set_token, calendar, token)

    async def unsent_documents(self) -> tuple[tuple[Document, Path], ...]:
        return await asyncio.to_thread(self._unsent_documents)

    async def document_sent(self, document_id: str) -> None:
        await asyncio.to_thread(self._document_sent, document_id)
