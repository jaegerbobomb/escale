"""Ticket documents on the user's Nextcloud (S009, SPEC § Documents, ADR-0004).

A document lives in ``Escale/documents/<sha256>/``: the file, unchanged, and a
``meta.json`` (schema.org ``DigitalDocument``), KDE Itinerary's layout. A reservation
points to its documents through schema.org ``subjectOf``, a list of their ids, as
KItinerary's ``DocumentUtil`` writes it. In Escale the ids are kept apart from the
JSON-LD (``ExtractedReservation.subject_of``); ``jsonld`` puts them back for the
calendar and ``split`` takes them out again.

A sync run uploads what the server lacks (S009a); ``Documents`` gets the copy a device
lacks, when it is opened and ahead for the current trip (S009b), and removes those of
past trips when the copies take more than ``LIMIT_BYTES`` (S009c).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from escale_core.extraction import Document, ExtractedReservation
from escale_core.nextcloud import FOLDER, NextcloudError, NextcloudServer

if TYPE_CHECKING:
    from escale_core.account import Account
    from escale_core.store import ReservationStore
    from escale_core.trips import Trip

SUBJECT_OF = "subjectOf"
LIMIT_BYTES = 500 * 1024 * 1024
"""How much the local copies of documents may take before past trips' go (S009c)."""


def folder(document_id: str) -> str:
    """The document's folder, relative to the user's files."""
    return f"{FOLDER}/documents/{document_id}"


def file_name(document: Document) -> str:
    return Path(document.name).name


def meta(document: Document) -> dict[str, str]:
    """What ``meta.json`` holds."""
    return {
        "@type": "DigitalDocument",
        "name": file_name(document),
        "encodingFormat": document.mime_type,
    }


def _listed(value: object) -> list[Any]:
    if value is None:
        return []
    return list(value) if isinstance(value, list) else [value]


def payload(raw: Mapping[str, Any], subject_of: Sequence[str]) -> dict[str, Any]:
    """The JSON-LD with the document ids in ``subjectOf``."""
    element = dict(raw)
    listed = _listed(element.get(SUBJECT_OF))
    extra = [d for d in subject_of if d not in listed]
    if extra:
        element[SUBJECT_OF] = listed + extra
    return element


def jsonld(reservation: ExtractedReservation) -> dict[str, Any]:
    """The reservation as the calendar holds it (S009a)."""
    return payload(reservation.raw, reservation.subject_of)


def split(element: Mapping[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    """The JSON-LD without its document ids, and the ids; anything else ``subjectOf``
    holds stays in the JSON-LD."""
    raw = dict(element)
    listed = _listed(raw.pop(SUBJECT_OF, None))
    ids = tuple(x for x in listed if isinstance(x, str))
    others = [x for x in listed if not isinstance(x, str)]
    if others:
        raw[SUBJECT_OF] = others
    return raw, ids


async def upload(server: NextcloudServer, document: Document, content: bytes) -> bool:
    """Put ``document`` on the server unless it is there; ``True`` when uploaded.

    ``meta.json`` goes last, so that a folder with one holds the whole document.
    """
    where = folder(document.id)
    if await server.file_exists(f"{where}/meta.json"):
        return False
    await server.put_file(f"{where}/{file_name(document)}", content, document.mime_type)
    described = json.dumps(meta(document), indent=2).encode()
    await server.put_file(f"{where}/meta.json", described, "application/json")
    return True


async def download(server: NextcloudServer, document_id: str) -> tuple[Document, bytes] | None:
    """The document and its content; ``None`` when the server does not have it whole, or
    when the content is not the one its id names."""
    where = folder(document_id)
    described = await server.get_file(f"{where}/meta.json")
    try:
        found = json.loads(described) if described is not None else None
    except ValueError:
        return None
    name = found.get("name") if isinstance(found, dict) else None
    if not isinstance(name, str) or not Path(name).name:
        return None
    content = await server.get_file(f"{where}/{Path(name).name}")
    if content is None or hashlib.sha256(content).hexdigest() != document_id:
        return None
    kind = found.get("encodingFormat") if isinstance(found, dict) else None
    mime_type = kind if isinstance(kind, str) else "application/octet-stream"
    return Document(document_id, Path(name).name, mime_type), content


class Documents:
    """The local copy of a document, downloaded when missing (S009b)."""

    def __init__(self, store: ReservationStore, account: Account) -> None:
        self._store, self._account = store, account

    async def _fetch(self, server: NextcloudServer, document_id: str) -> Path | None:
        found = await download(server, document_id)
        if found is None:
            return None
        await self._store.keep_document(*found)
        return self._store.document_path(document_id)

    async def local(self, document_id: str) -> Path | None:
        """The copy on this device, downloaded first if needed; ``None`` when it cannot
        be had now (no account, no network, not on the server)."""
        path = self._store.document_path(document_id)
        server = self._account.server
        if path is not None or server is None:
            return path
        try:
            return await self._fetch(server, document_id)
        except NextcloudError:
            return None

    async def prefetch(self, reservations: Iterable[ExtractedReservation]) -> int:
        """Download the documents of ``reservations`` the device lacks; how many came.
        Stops at the first network problem: the next run tries again."""
        server = self._account.server
        count = 0
        if server is None:
            return count
        missing = {
            d: None
            for r in reservations
            for d in r.subject_of
            if self._store.document_path(d) is None
        }
        try:
            for document_id in missing:
                if await self._fetch(server, document_id) is not None:
                    count += 1
        except NextcloudError:
            pass
        return count

    async def clean(self, trips: Sequence[Trip], now: datetime, limit: int = LIMIT_BYTES) -> int:
        """Over ``limit``, remove the copies of past trips' documents, oldest trip first,
        until under it; how many were removed (S009c). Kept: the current and coming
        trips' documents, those not on the server yet, and all of them without an
        account to download them again from."""
        if self._account.server is None:
            return 0
        sizes = {
            d.id: path.stat().st_size
            for d in await self._store.documents()
            if (path := self._store.document_path(d.id)) is not None
        }
        total = sum(sizes.values())
        if total <= limit:
            return 0
        kept = {d.id for d, _ in await self._store.unsent_documents()}
        kept |= {
            d for trip in trips if trip.end >= now for r in trip.reservations for d in r.subject_of
        }
        removed = 0
        for trip in sorted((t for t in trips if t.end < now), key=lambda t: t.end):
            for document_id in (d for r in trip.reservations for d in r.subject_of):
                if total <= limit:
                    return removed
                if document_id in kept or document_id not in sizes:
                    continue
                await self._store.forget_document(document_id)
                total -= sizes.pop(document_id)
                removed += 1
        return removed
