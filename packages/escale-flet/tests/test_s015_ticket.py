"""S015 — Full-screen ticket, offline."""

from __future__ import annotations

import asyncio
import base64
import io
import socket
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import flet as ft
import pytest
import segno
from PIL import Image
from pytest_bdd import given, scenarios, then, when

from escale_core.extraction import Document, ExtractedReservation
from escale_core.importer import reservation_from_jsonld
from escale_core.sqlite_store import SqliteReservationStore
from escale_core.tickets import Barcode
from escale_flet.barcode import MODULE_PX
from escale_flet.demo import LONDON_TRIP, LONDON_TRIP_FULL
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, button, texts, walk
from escale_flet.timeline import has_ticket

scenarios("S015.feature")

TOKEN = "qrCode:ESCALE-TEST-TICKET-0001"


def train(token: str | None) -> dict[str, Any]:
    ticket = {
        k: v
        for k, v in LONDON_TRIP[0]["reservedTicket"].items()
        if k not in ("ticketToken", "ticketNumber")
    }
    if token:
        ticket["ticketToken"] = token
        ticket["ticketNumber"] = "8542 1176 9033"
    return {**LONDON_TRIP[0], "reservedTicket": ticket}


@dataclass
class World:
    tmp: Path
    reservation: ExtractedReservation | None = None
    store: SqliteReservationStore = field(init=False)
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    shell: Shell | None = None

    def __post_init__(self) -> None:
        self.store = SqliteReservationStore(self.tmp / "data")

    def keep(self, element: dict[str, Any], with_pdf: bool = False) -> None:
        pdf = self.tmp / "ticket.pdf"
        pdf.write_bytes(b"%PDF-1.4 test ticket")
        r = reservation_from_jsonld(element, ("pdfdoc",))
        assert r is not None
        doc = Document("pdfdoc", "ticket.pdf", "application/pdf")
        asyncio.run(self.store.add(doc, [r], pdf if with_pdf else None))
        [self.reservation] = asyncio.run(self.store.reservations())

    def open_ticket(self) -> None:
        start = datetime.fromisoformat(LONDON_TRIP[0]["reservationFor"]["departureTime"])
        self.shell = Shell(store=self.store, clock=lambda: start)
        self.shell.mount(cast(ft.Page, self.page))
        assert self.reservation is not None
        asyncio.run(self.shell.show_ticket(self.reservation))


def shown_barcode(shell: Shell) -> tuple[Barcode, bytes]:
    [box] = [c for c in walk(shell.body) if isinstance(c.data, dict) and "barcode" in c.data]
    [image] = [c for c in walk(box) if isinstance(c, ft.Image)]
    return box.data["barcode"], base64.b64decode(cast(str, image.src))


def modules(png: bytes, size: int, quiet: int) -> list[list[int]]:
    """Read back the modules of a 2D code drawn by ``matrix_png``."""
    image = Image.open(io.BytesIO(png)).convert("1")
    centre = MODULE_PX // 2
    return [
        [
            int(
                image.getpixel(((x + quiet) * MODULE_PX + centre, (y + quiet) * MODULE_PX + centre))
                == 0
            )
            for x in range(size)
        ]
        for y in range(size)
    ]


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


@given("a stored train reservation whose ticket token is a QR code")
def stored_qr(world: World) -> None:
    world.keep(train(TOKEN))


@given("a stored reservation with a ticket token")
def stored_token(world: World) -> None:
    world.keep(train(TOKEN))


@given("a stored reservation without ticket token but with its PDF")
def stored_pdf(world: World) -> None:
    world.keep(train(None), with_pdf=True)


@when("the user opens its ticket")
def opens(world: World) -> None:
    world.open_ticket()


@when("the user opens its ticket with no network")
def opens_offline(world: World, monkeypatch: pytest.MonkeyPatch) -> None:
    def no_network(*_: Any, **__: Any) -> None:
        raise OSError("network disabled for this test")

    monkeypatch.setattr(socket.socket, "connect", no_network)
    world.open_ticket()


@then("the QR code is shown and encodes the ticket token's content")
def qr_encodes_token(world: World) -> None:
    assert world.shell is not None
    code, png = shown_barcode(world.shell)
    assert code == Barcode("qr", b"ESCALE-TEST-TICKET-0001")
    expected = [list(row) for row in segno.make(code.data, micro=False, error="m").matrix]
    assert modules(png, len(expected), quiet=4) == expected


@then("the train number, route, date, coach and seat are shown")
def details_shown(world: World) -> None:
    assert world.shell is not None
    shown = " | ".join(texts(world.shell.body))
    for expected in (
        "IC 9014",
        "Paris Gare du Nord → London St Pancras",
        "Wed 8 Jul 2026 · 08:01",
        "Coach 12 · Seat 41",
        "8542 1176 9033",
    ):
        assert expected in shown, expected


@then("the barcode is shown")
def barcode_shown(world: World) -> None:
    assert world.shell is not None
    _, png = shown_barcode(world.shell)
    assert png.startswith(b"\x89PNG")


@then("the view offers to open the PDF")
def offers_pdf(world: World) -> None:
    assert world.shell is not None
    assert not button(world.shell.body, "Open the original document").disabled


# --- details ---


def test_back_returns_to_the_trip(world: World) -> None:
    world.keep(train(TOKEN))
    world.open_ticket()
    assert world.shell is not None and world.page.appbar is not None
    assert world.page.navigation_bar is None
    asyncio.run(world.shell.close_ticket())
    assert world.shell.ticket is None
    assert world.page.appbar.leading is None


def test_no_document_and_no_barcode_disables_the_button(world: World) -> None:
    world.keep(train(None), with_pdf=False)
    world.open_ticket()
    assert world.shell is not None
    assert button(world.shell.body, "Open the original document").disabled


def test_timeline_card_has_a_ticket_button(world: World) -> None:
    world.keep(train(TOKEN))
    start = datetime.fromisoformat(LONDON_TRIP[0]["reservationFor"]["departureTime"])
    shell = Shell(store=world.store, clock=lambda: start)
    shell.mount(cast(ft.Page, world.page))
    asyncio.run(shell.refresh())
    ticket_button = button(shell.body, "Ticket")
    ticket_button.on_click(None)
    assert shell.ticket is not None


# --- a kept document is a ticket only for transport and events (0.11.1) ---

HOTEL, MUSEUM, DINNER = LONDON_TRIP_FULL[1], LONDON_TRIP_FULL[2], LONDON_TRIP_FULL[3]
CHECK_IN = datetime.fromisoformat(HOTEL["checkinTime"])


@given("a stored hotel booking without ticket token but with its PDF")
def stored_hotel(world: World) -> None:
    world.keep(HOTEL, with_pdf=True)


@when("the current trip is shown")
def trip_shown(world: World) -> None:
    world.shell = Shell(store=world.store, clock=lambda: CHECK_IN - timedelta(hours=1))
    world.shell.mount(cast(ft.Page, world.page))
    asyncio.run(world.shell.refresh())


@then('the booking\'s card has no "Ticket" button')
def no_ticket_button(world: World) -> None:
    assert world.shell is not None
    with pytest.raises(LookupError):
        button(world.shell.body, "Ticket")
    assert world.shell.current_ticket() is None


@then("its detail offers to open the booking document")
def detail_offers_document(world: World) -> None:
    assert world.shell is not None and world.reservation is not None
    world.shell.open_detail(world.reservation)
    assert not button(world.shell.body, "Booking document").disabled
    with pytest.raises(LookupError):
        button(world.shell.body, "Ticket")


@pytest.mark.parametrize(
    ("element", "expected"),
    [(train(None), True), (MUSEUM, True), (HOTEL, False), (DINNER, False)],
    ids=["train", "museum", "hotel", "restaurant"],
)
def test_a_kept_document_is_a_ticket_for_transport_and_events_only(
    element: dict[str, Any], expected: bool
) -> None:
    r = reservation_from_jsonld(element, ("pdfdoc",))
    assert r is not None
    assert has_ticket(r) is expected


def test_a_barcode_is_a_ticket_whatever_the_booking() -> None:
    r = reservation_from_jsonld({**DINNER, "reservedTicket": {"ticketToken": TOKEN}}, ())
    assert r is not None
    assert has_ticket(r)
