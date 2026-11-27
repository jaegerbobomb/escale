"""Ticket documents on the user's Nextcloud (S009, SPEC § Documents, ADR-0004).

A document lives in ``Escale/documents/<sha256>/``: the file, unchanged, and a
``meta.json`` (schema.org ``DigitalDocument``), KDE Itinerary's layout. A reservation
points to its documents through schema.org ``subjectOf``, a list of their ids, as
KItinerary's ``DocumentUtil`` writes it. In Escale the ids are kept apart from the
JSON-LD (``ExtractedReservation.subject_of``); ``jsonld`` puts them back for the
calendar and ``split`` takes them out again.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from escale_core.extraction import Document, ExtractedReservation
from escale_core.nextcloud import FOLDER, NextcloudServer

SUBJECT_OF = "subjectOf"


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
