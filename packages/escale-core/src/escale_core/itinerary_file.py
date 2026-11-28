"""Reading a KDE Itinerary export, an ``.itinerary`` file (S028).

The file is a zip laid out as KItinerary's ``File`` class writes it (read in its source,
``src/lib/file.cpp``, and in KDE Itinerary's ``src/app/importexport.cpp``):

- ``reservations/<id>.json``: one schema.org reservation, as an object or an array of
  one; its documents are named in ``subjectOf``;
- ``documents/<id>/meta.json`` (``name``, ``encodingFormat``) and the file it names;
- ``passes/<passTypeId>/<serial>.pkpass``;
- ``custom/<domain>/<id>``: KDE Itinerary's own data (trips, transfers, program
  memberships, health certificates, settings, …).

Escale takes the reservations and the documents, ids unchanged, and says what it leaves
out. KDE Itinerary keeps no batch in the file: it puts batches together again on import,
and so does Escale's store, by identity. Only the standard ``zipfile`` module is used, so
that this also works where no extractor runs (Android).
"""

from __future__ import annotations

import json
import mimetypes
import re
import zipfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from escale_core.documents import split
from escale_core.extraction import Document, ExtractedReservation, ExtractionResult
from escale_core.importer import reservation_from_jsonld

SUFFIX = ".itinerary"
MAX_ENTRY_BYTES = 64 * 1024 * 1024
"""A larger entry is left out: an export holds tickets, not videos."""

_RESERVATION = re.compile(r"^reservations/[^/]+\.json$")
_META = re.compile(r"^documents/([^/]+)/meta\.json$")
_LEFT_OUT = (
    (re.compile(r"^passes/[^/]+/[^/]+\.pkpass$"), "pass"),
    (re.compile(r"^custom/org\.kde\.itinerary/programs/[^/]+$"), "program membership"),
    (re.compile(r"^custom/org\.kde\.itinerary/health-certificates/[^/]+$"), "health certificate"),
)
_SETTINGS = re.compile(r"^custom/org\.kde\.itinerary/settings/")


def _json(z: zipfile.ZipFile, info: zipfile.ZipInfo) -> Any:
    if info.file_size > MAX_ENTRY_BYTES:
        return None
    try:
        return json.loads(z.read(info))
    except (ValueError, zipfile.BadZipFile):
        return None


def _element(found: Any) -> Mapping[str, Any] | None:
    if isinstance(found, list) and len(found) == 1:
        found = found[0]
    return found if isinstance(found, Mapping) else None


def _document(z: zipfile.ZipFile, doc_id: str, meta: Any) -> tuple[Document, bytes] | None:
    if not isinstance(meta, Mapping) or not isinstance(meta.get("name"), str):
        return None
    name = Path(meta["name"]).name
    try:
        info = z.getinfo(f"documents/{doc_id}/{name}")
    except KeyError:
        return None
    if not name or info.file_size > MAX_ENTRY_BYTES:
        return None
    kind = meta.get("encodingFormat")
    mime_type = kind if isinstance(kind, str) else mimetypes.guess_type(name)[0]
    return Document(doc_id, name, mime_type or "application/octet-stream"), z.read(info)


def _plural(n: int, word: str) -> str:
    if n == 1:
        return f"1 {word}"
    return f"{n} {word}{'es' if word.endswith('s') else 's'}"


def read_itinerary(path: Path) -> ExtractionResult:
    """The reservations and documents of an export; an error result if it is not one."""
    try:
        with zipfile.ZipFile(path) as z:
            infos = sorted(z.infolist(), key=lambda i: i.filename)
            reservations: list[ExtractedReservation] = []
            documents: list[tuple[Document, bytes]] = []
            counts = {word: 0 for _, word in _LEFT_OUT}
            settings = False
            for info in infos:
                name = info.filename
                if _RESERVATION.match(name):
                    element = _element(_json(z, info))
                    r = reservation_from_jsonld(*split(element)) if element else None
                    if r is not None:
                        reservations.append(r)
                elif meta := _META.match(name):
                    found = _document(z, meta[1], _json(z, info))
                    if found is not None:
                        documents.append(found)
                elif _SETTINGS.match(name):
                    settings = True
                else:
                    for pattern, word in _LEFT_OUT:
                        if pattern.match(name):
                            counts[word] += 1
    except (zipfile.BadZipFile, OSError):
        return ExtractionResult(document=None, error=f"{path.name} is not a KDE Itinerary export.")
    left_out = [_plural(n, word) for word, n in counts.items() if n]
    if settings:
        left_out.append("settings")
    return ExtractionResult(
        document=None,
        reservations=tuple(reservations),
        documents=tuple(documents),
        not_imported=tuple(left_out),
    )
