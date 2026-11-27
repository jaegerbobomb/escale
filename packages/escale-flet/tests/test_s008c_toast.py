"""S008c — the user is told when a change of theirs gave way to one made elsewhere."""

from __future__ import annotations

import asyncio
from typing import cast

import flet as ft

from escale_core.importer import reservation_from_jsonld
from escale_core.sync import SyncReport
from escale_flet.demo import LONDON_TRIP
from escale_flet.shell import Shell, changed_elsewhere
from escale_flet.testing import FakePage, texts


def shell_with(report: SyncReport) -> tuple[Shell, FakePage]:
    async def sync() -> SyncReport:
        return report

    page = FakePage(width=1000)
    shell = Shell(sync=sync)
    shell.mount(cast(ft.Page, page))
    return shell, page


def test_one_reservation_is_named() -> None:
    hotel = reservation_from_jsonld(LONDON_TRIP[1], ())
    assert hotel is not None
    shell, page = shell_with(SyncReport(received=1, changed_elsewhere=(hotel,)))
    asyncio.run(shell.synchronise())
    assert isinstance(page.dialog, ft.SnackBar)
    assert page.dialog.behavior == ft.SnackBarBehavior.FLOATING
    assert texts(page.dialog) == [
        "The Hoxton, Holborn was changed on another device; that version is kept."
    ]


def test_several_are_counted() -> None:
    assert changed_elsewhere(("A", "B")) == (
        "2 reservations were changed on another device; those versions are kept."
    )


def test_no_conflict_no_toast() -> None:
    shell, page = shell_with(SyncReport(received=1))
    asyncio.run(shell.synchronise())
    assert page.dialog is None
