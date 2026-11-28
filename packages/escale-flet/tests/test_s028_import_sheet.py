"""S028 — the confirmation of a KDE Itinerary export says what comes and what does not."""

from __future__ import annotations

from pathlib import Path

import flet as ft

from escale_core.itinerary_file import read_itinerary
from escale_flet.demo import demo_export
from escale_flet.import_sheet import confirmation_sheet
from escale_flet.testing import texts, walk


def test_documents_and_what_is_left_out_are_said(tmp_path: Path) -> None:
    result = read_itinerary(demo_export(tmp_path / "e.itinerary"))
    sheet = confirmation_sheet(result, lambda _: None, lambda _: None)
    shown = texts(sheet)
    assert "2 reservations found" in shown
    assert "With 2 documents." in shown
    assert "Not imported: 1 pass, settings." in shown


def test_many_reservations_scroll(tmp_path: Path) -> None:
    result = read_itinerary(demo_export(tmp_path / "e.itinerary"))
    many = type(result)(None, result.reservations * 3)
    sheet = confirmation_sheet(many, lambda _: None, lambda _: None)
    [body] = [c for c in walk(sheet) if isinstance(c.data, dict) and "sheet_body" in c.data]
    assert isinstance(body, ft.Column) and body.scroll == ft.ScrollMode.AUTO
