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

from escale_core.account import Account
from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.documents import Documents
from escale_core.extraction import Document
from escale_core.importer import Importer, reservation_from_jsonld
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.store import InMemoryReservationStore
from escale_flet.import_sheet import phone_sheet
from escale_flet.shell import NOT_ON_DEVICE, Shell, changed_elsewhere, toast

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


_TRAVELLERS = [{"@type": "Person", "name": "Jane Doe"}, {"@type": "Person", "name": "Alex Martin"}]

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
        "reservationStatus": "http://schema.org/ReservationConfirmed",
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

STAY_DETAILS: dict[str, Any] = {
    "lodgingUnitDescription": "Cosy room, one double bed",
    "potentialAction": {
        "@type": "UpdateAction",
        "target": "https://secure.booking.com/myreservations.html",
    },
}
"""What a Booking.com confirmation adds to the stay (S017a); the contact is made up."""

LONDON_TRIP_FULL: list[dict[str, Any]] = [
    LONDON_TRIP[0],
    {
        **LONDON_TRIP[1],
        **STAY_DETAILS,
        "reservationFor": {
            **LONDON_TRIP[1]["reservationFor"],
            "telephone": "+44 20 7946 0000",
            "email": "stay@example.com",
        },
    },
    {
        "@type": "EventReservation",
        "reservationNumber": "ESC-E1",
        "underName": _TRAVELLERS,
        "reservationFor": {
            "@type": "Event",
            "name": "Tate Modern",
            "startDate": "2026-07-09T11:00:00+01:00",
            "location": _place("Place", "Tate Modern", "London", "Bankside"),
        },
    },
    {
        "@type": "FoodEstablishmentReservation",
        "reservationNumber": "ESC-F1",
        "underName": _TRAVELLERS,
        "startTime": "2026-07-09T19:30:00+01:00",
        "reservationFor": _place(
            "FoodEstablishment", "Dishoom Covent Garden", "London", "12 Upper St Martin's Lane"
        ),
    },
    LONDON_TRIP[2],
]
"""The same trip with a museum and a dinner: five segments (S011)."""

FLIGHT: dict[str, Any] = {
    "@type": "FlightReservation",
    "reservationNumber": "ESC-F718",
    "underName": _TRAVELLERS[:1],
    "reservedTicket": {
        "@type": "Ticket",
        "ticketedSeat": {"@type": "Seat", "seatNumber": "23A"},
        "ticketToken": "pdf417:ESCALE-DEMO-AF718-JANE-DOE",
    },
    "reservationFor": {
        "@type": "Flight",
        "airline": {"@type": "Airline", "iataCode": "AF"},
        "flightNumber": "718",
        "departureAirport": {
            "@type": "Airport",
            "iataCode": "CDG",
            "name": "Paris Charles de Gaulle",
        },
        "departureTime": "2026-09-14T10:25:00+02:00",
        "arrivalAirport": {"@type": "Airport", "iataCode": "LHR", "name": "London Heathrow"},
        "arrivalTime": "2026-09-14T10:45:00+01:00",
    },
}
"""A synthetic flight for screenshots and tests (S016); no real booking."""

ROUTES: dict[str, list[dict[str, Any]] | None] = {
    "/import-found": [SAMPLE],
    "/import-nothing": [],
    "/import-phone": None,
    "/trip": None,
    "/ticket": None,
    "/trip-jump": None,
    "/trip-detail": None,
    "/flight-detail": None,
    "/stay-detail": None,
    "/stay-editor": None,
    "/preferences": None,
    "/preferences-refused": None,
    "/preferences-connected": None,
    "/changed-elsewhere": None,
    "/document-not-here": None,
}
"""Demo route -> what the extractor returns (``None``: no import sheet).

``/trip`` shows the synthetic London trip in "Current", 40 minutes before it starts;
``/ticket`` opens its first train's ticket; ``/flight-detail`` opens a flight's detail,
``/stay-detail`` the hotel's,
``/stay-editor`` its editor; ``/preferences*`` the preferences, empty, after a refused
password, and connected to a fake Nextcloud (S006b); ``/changed-elsewhere`` the trip with
the toast of a change that gave way to one made on another device (S008c);
``/document-not-here`` the hotel's detail, offline, after "Booking document" was clicked
for a document not on the device (S009b).
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
    trip_routes = (
        "/trip",
        "/ticket",
        "/trip-jump",
        "/trip-detail",
        "/stay-detail",
        "/stay-editor",
        "/changed-elsewhere",
        "/document-not-here",
    )
    if route in trip_routes:
        found = [reservation_from_jsonld(e, ("demo",)) for e in LONDON_TRIP_FULL]
        await store.add(Document("demo", "ticket.pdf", "application/pdf"), [r for r in found if r])
        # 40 minutes before the first train leaves.
        start = datetime.fromisoformat(LONDON_TRIP[0]["reservationFor"]["departureTime"])
        clock = lambda: start - timedelta(minutes=40)  # noqa: E731
    elif route == "/flight-detail":
        [flight] = [r for r in [reservation_from_jsonld(FLIGHT, ("demo",))] if r]
        await store.add(Document("demo", "boarding-pass.pdf", "application/pdf"), [flight])
        leaves = datetime.fromisoformat(FLIGHT["reservationFor"]["departureTime"])
        clock = lambda: leaves - timedelta(hours=2)  # noqa: E731
    server = FakeNextcloud(["Personal", "Work"], password_ok=route != "/preferences-refused")
    account = Account(
        SettingsFile(ticket.parent / "settings.json"),
        MemoryPasswords(lasting=True),
        lambda url, login, password: server,
    )
    if route in ("/preferences-refused", "/preferences-connected", "/document-not-here"):
        await account.connect("cloud.example.org", "jane", "demo-app-password")
    if account.calendars:
        await account.choose(account.calendars[0])
    shell = Shell(
        importer=Importer(FakeExtractor(elements or []), store),
        choose_file=choose_file,
        clock=clock,
        account=account,
        documents=Documents(store, account),
    )
    shell.mount(page)
    await shell.refresh()
    if route == "/import-phone":
        page.show_dialog(phone_sheet(shell._close_sheet))
    elif route == "/ticket" and shell.trip is not None:
        await shell.show_ticket(shell.trip.reservations[0])
    elif route == "/trip-jump":
        await shell.jump("ESC-E1")
    elif route == "/trip-detail" and shell.trip is not None:
        shell.open_detail(shell.trip.reservations[-1])
    elif route == "/stay-detail" and shell.trip is not None:
        shell.open_detail(shell.trip.reservations[1])
    elif route == "/stay-editor" and shell.trip is not None:
        shell.open_detail(shell.trip.reservations[1])
        shell.edit_stay()
    elif route == "/document-not-here" and shell.trip is not None:
        server.reachable = False
        shell.open_detail(shell.trip.reservations[1])
        page.show_dialog(toast(NOT_ON_DEVICE, page.width, duration=60_000))
    elif route == "/changed-elsewhere":
        text = changed_elsewhere(["The Hoxton, Holborn"])
        page.show_dialog(toast(text, page.width, duration=60_000))
    elif route.startswith("/preferences"):
        await shell.open_preferences()
        if route == "/preferences-refused" and shell.preferences is not None:
            shell.preferences.draft.update(
                url="cloud.example.org", login="jane", password="demo-app-password"
            )
            shell.preferences.render()
    elif route == "/flight-detail" and shell.trip is not None:
        shell.open_detail(shell.trip.reservations[0])
    elif elements is not None and route not in trip_routes:
        await shell.start_import()
