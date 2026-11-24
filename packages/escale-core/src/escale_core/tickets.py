"""The ticket inside a reservation: its barcode and number (S015).

Token prefixes follow KItinerary (``datatypes/token.cpp``): ``qrcode:``, ``qrcodebin:``,
``azteccode:``, ``aztecbin:``, ``pdf417:``, ``pdf417bin:``, ``barcode128:``,
``datamatrix:``, case-insensitive; the ``bin`` forms are base64.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal

from escale_core.extraction import ExtractedReservation

BarcodeKind = Literal["qr", "aztec", "pdf417", "code128", "datamatrix"]

_TEXT: dict[str, BarcodeKind] = {
    "qrcode:": "qr",
    "azteccode:": "aztec",
    "pdf417:": "pdf417",
    "barcode128:": "code128",
    "datamatrix:": "datamatrix",
}
_BINARY: dict[str, BarcodeKind] = {
    "qrcodebin:": "qr",
    "aztecbin:": "aztec",
    "pdf417bin:": "pdf417",
}


@dataclass(frozen=True)
class Barcode:
    kind: BarcodeKind
    data: bytes


@dataclass(frozen=True)
class Ticket:
    barcode: Barcode | None
    number: str | None


def parse_token(token: str) -> Barcode | None:
    """The barcode a ticket token describes; ``None`` if unknown or unreadable."""
    lower = token.lower()
    for prefix, kind in _BINARY.items():
        if lower.startswith(prefix):
            try:
                return Barcode(kind, base64.b64decode(token[len(prefix) :], validate=True))
            except (binascii.Error, ValueError):
                return None
    for prefix, kind in _TEXT.items():
        if lower.startswith(prefix):
            return Barcode(kind, token[len(prefix) :].encode("utf-8"))
    return None


def ticket_of(reservation: ExtractedReservation) -> Ticket:
    ticket = reservation.raw.get("reservedTicket")
    ticket = ticket if isinstance(ticket, Mapping) else {}
    token = ticket.get("ticketToken")
    number = ticket.get("ticketNumber")
    return Ticket(
        barcode=parse_token(token) if isinstance(token, str) else None,
        number=number if isinstance(number, str) and number else None,
    )
