"""S009b — a document that is not on the device downloads when opened, and the current
trip's documents come ahead."""

from __future__ import annotations

import asyncio
import hashlib
from collections.abc import Sequence
from datetime import datetime, timedelta
from pathlib import Path
from typing import cast

import flet as ft
import pytest

from escale_core.account import Account
from escale_core.adapters.fake_nextcloud import FakeNextcloud
from escale_core.documents import Documents, folder
from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.passwords import MemoryPasswords
from escale_core.settings import SettingsFile
from escale_core.store import InMemoryReservationStore
from escale_core.sync import SyncReport
from escale_core.trips import Trip
from escale_flet.demo import LONDON_TRIP
from escale_flet.shell import NOT_ON_DEVICE, Shell
from escale_flet.testing import FakePage, action, click, texts

HOTEL = LONDON_TRIP[1]
CHECK_IN = datetime.fromisoformat(HOTEL["checkinTime"])
PDF = b"%PDF-1.7\r\nbooking\n"
DOC = Document(hashlib.sha256(PDF).hexdigest(), "booking.pdf", "application/pdf")


def setting(tmp_path: Path) -> tuple[Shell, FakePage, FakeNextcloud, list[str]]:
    server = FakeNextcloud(["Personal"], {"Escale"})
    server.files[f"{folder(DOC.id)}/meta.json"] = (
        b'{"@type": "DigitalDocument", "name": "booking.pdf", "encodingFormat": "application/pdf"}'
    )
    server.files[f"{folder(DOC.id)}/booking.pdf"] = PDF
    account = Account(SettingsFile(tmp_path / "s.json"), MemoryPasswords(True), lambda *_: server)
    assert asyncio.run(account.connect("cloud.example.org", "jane", "pw"))
    store = InMemoryReservationStore()
    hotel = reservation_from_jsonld(HOTEL, (DOC.id,))  # received from another device
    assert hotel is not None
    asyncio.run(store.add(DOC, [hotel]))
    opened: list[str] = []

    async def launch(url: str) -> None:
        opened.append(url)

    async def sync() -> SyncReport:
        return SyncReport()

    shell = Shell(
        store=store,
        clock=lambda: CHECK_IN - timedelta(hours=1),
        launch=launch,
        account=account,
        sync=sync,
        documents=Documents(store, account),
    )
    page = FakePage(width=1000)
    shell.mount(cast(ft.Page, page))
    asyncio.run(shell.refresh())
    assert shell.trip is not None
    return shell, page, server, opened


def test_a_document_downloads_when_opened(tmp_path: Path) -> None:
    shell, _, _, opened = setting(tmp_path)
    assert shell.trip is not None
    shell.open_detail(shell.trip.reservations[0])
    click(action(shell.body, "Booking document"))
    [url] = opened
    assert Path(url.removeprefix("file://")).read_bytes() == PDF


def test_offline_a_toast_says_it_is_not_here(tmp_path: Path) -> None:
    shell, page, server, opened = setting(tmp_path)
    server.reachable = False
    assert shell.trip is not None
    shell.open_detail(shell.trip.reservations[0])
    click(action(shell.body, "Booking document"))
    assert opened == []
    assert isinstance(page.dialog, ft.SnackBar)
    assert texts(page.dialog) == [NOT_ON_DEVICE]


def test_without_an_account_the_document_cannot_be_opened(tmp_path: Path) -> None:
    store = InMemoryReservationStore()
    hotel = reservation_from_jsonld(HOTEL, (DOC.id,))
    assert hotel is not None
    asyncio.run(store.add(DOC, [hotel]))
    account = Account(
        SettingsFile(tmp_path / "s.json"), MemoryPasswords(True), lambda *_: FakeNextcloud()
    )
    shell = Shell(
        store=store,
        clock=lambda: CHECK_IN - timedelta(hours=1),
        account=account,
        documents=Documents(store, account),
    )
    shell.mount(cast(ft.Page, FakePage(width=1000)))
    asyncio.run(shell.refresh())
    assert shell.trip is not None
    shell.open_detail(shell.trip.reservations[0])
    assert "Booking document" not in texts(shell.body)


def test_a_sync_brings_the_current_trip_documents(tmp_path: Path) -> None:
    shell, _, server, _ = setting(tmp_path)
    asyncio.run(shell.synchronise())
    server.reachable = False
    assert shell.store.document_path(DOC.id) is not None


def test_a_sync_cleans_past_documents(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """S009c: after a run, the cleaning gets every trip and the clock's time."""
    shell, _, _, _ = setting(tmp_path)
    seen: list[tuple[int, datetime]] = []

    async def clean(trips: Sequence[Trip], now: datetime, limit: int = 0) -> int:
        seen.append((len(trips), now))
        return 0

    assert shell.documents is not None
    monkeypatch.setattr(shell.documents, "clean", clean)
    asyncio.run(shell.synchronise())
    assert seen == [(1, CHECK_IN - timedelta(hours=1))]
