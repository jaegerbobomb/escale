"""Demo mode for screenshots: ``ESCALE_DEMO=1`` opens the import sheets by route.

The UI is drawn on a canvas, so the screenshot tool cannot click through a file chooser;
in demo mode these routes open the sheet on a synthetic ticket instead. Nothing here
runs unless the variable is set.
"""

from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import flet as ft

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.extraction import Document
from escale_core.importer import Importer, reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.import_sheet import phone_sheet
from escale_flet.shell import Shell

SAMPLE: dict[str, Any] = {
    "@context": "http://schema.org",
    "@type": "TrainReservation",
    "reservationNumber": "ESCDEMO",
    "underName": [
        {"@type": "Person", "name": "Jane Doe"},
        {"@type": "Person", "name": "John Doe"},
    ],
    "reservationFor": {
        "@type": "TrainTrip",
        "trainNumber": "IC 123",
        "departureStation": {"@type": "TrainStation", "name": "Lyon Part-Dieu"},
        "departureTime": "2027-03-14T08:04:00+01:00",
        "arrivalStation": {"@type": "TrainStation", "name": "Paris Gare de Lyon"},
        "arrivalTime": "2027-03-14T10:00:00+01:00",
    },
}


def _place(kind: str, name: str, town: str, street: str | None = None) -> dict[str, Any]:
    address: dict[str, Any] = {"@type": "PostalAddress", "addressLocality": town}
    if street:
        address["streetAddress"] = street
    return {"@type": kind, "name": name, "address": address}


_TRAVELLERS = [{"@type": "Person", "name": "Jane Doe"}, {"@type": "Person", "name": "John Doe"}]

LONDON_TRIP: list[dict[str, Any]] = [
    {
        "@type": "TrainReservation",
        "reservationNumber": "ESC-T1",
        "underName": _TRAVELLERS,
        "reservedTicket": {
            "@type": "Ticket",
            "ticketedSeat": {"@type": "Seat", "seatSection": "12", "seatNumber": "41"},
            "ticketToken": "qrCode:ESCALE-DEMO-IC9014-JANE-DOE",
            "ticketNumber": "8542 1176 9033",
        },
        "reservationFor": {
            "@type": "TrainTrip",
            "trainNumber": "IC 9014",
            "departureStation": _place("TrainStation", "Paris Gare du Nord", "Paris"),
            "departurePlatform": "4",
            "departureTime": "2026-07-08T08:01:00+02:00",
            "arrivalStation": _place("TrainStation", "London St Pancras", "London"),
            "arrivalTime": "2026-07-08T09:30:00+01:00",
        },
    },
    {
        "@type": "LodgingReservation",
        "reservationNumber": "ESC-H1",
        "underName": _TRAVELLERS,
        "reservationFor": _place(
            "LodgingBusiness", "The Hoxton, Holborn", "London", "199-206 High Holborn"
        ),
        "checkinTime": "2026-07-08T15:00:00+01:00",
        "checkoutTime": "2026-07-10T11:00:00+01:00",
    },
    {
        "@type": "TrainReservation",
        "reservationNumber": "ESC-T2",
        "underName": _TRAVELLERS,
        "reservationFor": {
            "@type": "TrainTrip",
            "trainNumber": "IC 9039",
            "departureStation": _place("TrainStation", "London St Pancras", "London"),
            "departureTime": "2026-07-10T17:04:00+01:00",
            "arrivalStation": _place("TrainStation", "Paris Gare du Nord", "Paris"),
            "arrivalTime": "2026-07-10T20:30:00+02:00",
        },
    },
]
"""A synthetic trip for screenshots and tests; no real booking."""

ROUTES: dict[str, list[dict[str, Any]] | None] = {
    "/import-found": [SAMPLE],
    "/import-nothing": [],
    "/import-phone": None,
    "/trip": None,
    "/ticket": None,
}
"""Demo route -> what the extractor returns (``None``: no import sheet).

``/trip`` shows the synthetic London trip in "Current", 40 minutes before it starts;
``/ticket`` opens its first train's ticket.
"""


def enabled() -> bool:
    return os.environ.get("ESCALE_DEMO") == "1"


async def run(page: ft.Page) -> None:
    """Mount the shell and open the sheet that ``page.route`` names."""
    elements = ROUTES.get(page.route.rstrip("/"))
    ticket = Path(tempfile.mkdtemp(prefix="escale-demo-")) / "ticket.pdf"
    ticket.write_bytes(b"%PDF-1.4 demo")

    async def choose_file() -> Path | None:
        return ticket

    route = page.route.rstrip("/")
    store = InMemoryReservationStore()
    clock = None
    if route in ("/trip", "/ticket"):
        found = [reservation_from_jsonld(e, ("demo",)) for e in LONDON_TRIP]
        await store.add(Document("demo", "ticket.pdf", "application/pdf"), [r for r in found if r])
        # 40 minutes before the first train leaves.
        start = datetime.fromisoformat(LONDON_TRIP[0]["reservationFor"]["departureTime"])
        clock = lambda: start - timedelta(minutes=40)  # noqa: E731
    shell = Shell(
        importer=Importer(FakeExtractor(elements or []), store),
        choose_file=choose_file,
        clock=clock,
    )
    shell.mount(page)
    await shell.refresh()
    if route == "/import-phone":
        page.show_dialog(phone_sheet(shell._close_sheet))
    elif route == "/ticket" and shell.trip is not None:
        await shell.show_ticket(shell.trip.reservations[0])
    elif elements is not None and route not in ("/trip", "/ticket"):
        await shell.start_import()
