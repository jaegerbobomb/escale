"""Ticket tokens as kitinerary prints them (KItinerary's datatypes/token.cpp, 23.08)."""

from __future__ import annotations

import base64

import pytest

from escale_core.importer import reservation_from_jsonld
from escale_core.tickets import Barcode, parse_token, ticket_of


@pytest.mark.parametrize(
    ("token", "kind", "data"),
    [
        ("qrCode:HELLO 123", "qr", b"HELLO 123"),
        ("QRCODE:x", "qr", b"x"),
        ("qrcodebin:" + base64.b64encode(b"\x00\x01").decode(), "qr", b"\x00\x01"),
        ("aztecCode:ABC", "aztec", b"ABC"),
        ("aztecbin:" + base64.b64encode(b"\xff\x10").decode(), "aztec", b"\xff\x10"),
        ("pdf417:M1DOE/JANE", "pdf417", b"M1DOE/JANE"),
        ("pdf417bin:" + base64.b64encode(b"\x02").decode(), "pdf417", b"\x02"),
        ("barcode128:12345678", "code128", b"12345678"),
        ("dataMatrix:DM", "datamatrix", b"DM"),
    ],
)
def test_known_tokens(token: str, kind: str, data: bytes) -> None:
    assert parse_token(token) == Barcode(kind, data)  # type: ignore[arg-type]


@pytest.mark.parametrize("token", ["", "https://example.org/ticket", "aztecbin:@@not base64@@"])
def test_unknown_or_broken_tokens(token: str) -> None:
    assert parse_token(token) is None


def test_ticket_of_a_reservation() -> None:
    r = reservation_from_jsonld(
        {
            "@type": "TrainReservation",
            "reservedTicket": {
                "@type": "Ticket",
                "ticketToken": "qrCode:TICKET-1",
                "ticketNumber": "8542 1176 9033",
            },
            "reservationFor": {"@type": "TrainTrip"},
        },
        ("doc",),
    )
    assert r is not None
    ticket = ticket_of(r)
    assert ticket.barcode == Barcode("qr", b"TICKET-1")
    assert ticket.number == "8542 1176 9033"


def test_reservation_without_ticket() -> None:
    r = reservation_from_jsonld({"@type": "TrainReservation"}, ("doc",))
    assert r is not None
    assert ticket_of(r).barcode is None
