"""Demo mode for screenshots: ``ESCALE_DEMO=1`` opens the import sheets by route.

The UI is drawn on a canvas, so the screenshot tool cannot click through a file chooser;
in demo mode these routes open the sheet on a synthetic ticket instead. Nothing here
runs unless the variable is set.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any

import flet as ft

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.importer import Importer
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

ROUTES: dict[str, list[dict[str, Any]] | None] = {
    "/import-found": [SAMPLE],
    "/import-nothing": [],
    "/import-phone": None,
}
"""Demo route -> what the extractor returns (``None``: the phone explanation)."""


def enabled() -> bool:
    return os.environ.get("ESCALE_DEMO") == "1"


async def run(page: ft.Page) -> None:
    """Mount the shell and open the sheet that ``page.route`` names."""
    elements = ROUTES.get(page.route.rstrip("/"))
    ticket = Path(tempfile.mkdtemp(prefix="escale-demo-")) / "ticket.pdf"
    ticket.write_bytes(b"%PDF-1.4 demo")

    async def choose_file() -> Path | None:
        return ticket

    shell = Shell(
        importer=Importer(FakeExtractor(elements or []), InMemoryReservationStore()),
        choose_file=choose_file,
    )
    shell.mount(page)
    if page.route.rstrip("/") == "/import-phone":
        page.show_dialog(phone_sheet(shell._close_sheet))
    elif elements is not None:
        await shell.start_import()
