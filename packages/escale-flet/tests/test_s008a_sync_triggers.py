"""S008a — when the app sends its changes: after an import, an edit, a calendar choice."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast

import flet as ft

from escale_core.account import Account
from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.extraction import Document
from escale_core.importer import Importer, reservation_from_jsonld
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.stays import fields_of
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import LONDON_TRIP
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, button, click, tagged

DATA = Path(__file__).parents[2] / "escale-core" / "tests" / "data"


class Counter:
    def __init__(self) -> None:
        self.runs = 0

    async def __call__(self) -> None:
        self.runs += 1


def test_an_import_is_sent() -> None:
    synced = Counter()
    store = InMemoryReservationStore()
    extractor = FakeExtractor(json.loads((DATA / "train-booking.extracted.json").read_text()))

    async def choose_file() -> Path | None:
        return DATA / "train-booking.html"

    page = FakePage(width=1000)
    shell = Shell(importer=Importer(extractor, store), choose_file=choose_file, sync=synced)
    shell.mount(cast(ft.Page, page))
    asyncio.run(shell.start_import())
    click(button(page.dialog, "Add to trip"))
    assert synced.runs == 1


def test_an_edit_is_sent() -> None:
    synced = Counter()
    hotel = reservation_from_jsonld(LONDON_TRIP[1], ("d",))
    assert hotel is not None
    store = InMemoryReservationStore()
    asyncio.run(store.add(Document("d", "b.pdf", "application/pdf"), [hotel]))
    check_in = datetime.fromisoformat(LONDON_TRIP[1]["checkinTime"])
    shell = Shell(store=store, clock=lambda: check_in - timedelta(hours=1), sync=synced)
    shell.mount(cast(ft.Page, FakePage(width=1000)))
    asyncio.run(shell.refresh())
    assert shell.trip is not None
    shell.open_detail(shell.trip.reservations[0])
    asyncio.run(shell.save_stay(replace(fields_of(hotel), name="The Hoxton")))
    assert synced.runs == 1


def test_choosing_a_calendar_is_followed_by_a_sync(tmp_path: Path) -> None:
    synced = Counter()
    server = FakeNextcloud(["Personal", "Work"])
    account = Account(SettingsFile(tmp_path / "s.json"), MemoryPasswords(True), lambda *_: server)
    asyncio.run(account.connect("cloud.example.org", "jane", "pw"))
    page = FakePage(width=1000)
    shell = Shell(account=account, sync=synced)
    shell.mount(cast(ft.Page, page))
    asyncio.run(shell.open_preferences())
    group: Any = tagged(page.dialog, "calendars")
    group.value = server.calendar_url("Work")
    asyncio.run(group.on_change(None))
    assert synced.runs == 1
