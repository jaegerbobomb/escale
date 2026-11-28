"""S025a — "Open with Escale" on Linux: the desktop entry and ``escale FILE``."""

from __future__ import annotations

import asyncio
import configparser
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.importer import Importer
from escale_core.store import InMemoryReservationStore
from escale_flet.app import APP_ID, parse_args
from escale_flet.demo import demo_export
from escale_flet.shell import IMPORT_EXTENSIONS, Shell
from escale_flet.testing import FakePage, texts

ROOT = Path(__file__).parents[3]
PACKAGING = ROOT / "packaging" / "linux"
DATA = Path(__file__).parents[2] / "escale-core" / "tests" / "data"
TRAIN_JSONLD: list[dict[str, Any]] = json.loads(
    (DATA / "train-booking.extracted.json").read_text(encoding="utf-8")
)

scenarios("S025a.feature")


def shell_for(extractor: FakeExtractor) -> tuple[Shell, FakePage]:
    page = FakePage(width=1000)
    shell = Shell(importer=Importer(extractor, InMemoryReservationStore()))
    shell.mount(cast(ft.Page, page))
    return shell, page


@pytest.fixture
def world() -> dict[str, Any]:
    return {}


@given("a ticket PDF in the Files app")
def a_pdf(world: dict[str, Any], tmp_path: Path) -> None:
    pdf = tmp_path / "ticket.pdf"
    pdf.write_bytes(b"%PDF-1.7 ticket")
    world["file"], world["extractor"] = pdf, FakeExtractor(TRAIN_JSONLD)


@given("an `.itinerary` file")
def an_export(world: dict[str, Any], tmp_path: Path) -> None:
    world["file"], world["extractor"] = demo_export(tmp_path / "e.itinerary"), FakeExtractor([])


@when('the user chooses "Open with Escale"')
@when("the user opens it with Escale")
def opened(world: dict[str, Any]) -> None:
    args = parse_args([str(world["file"])])
    shell, page = shell_for(world["extractor"])
    asyncio.run(shell.open_file(args.file))
    world["page"] = page


@then("Escale shows the import confirmation for that file")
def confirmation(world: dict[str, Any]) -> None:
    page: FakePage = world["page"]
    assert isinstance(page.dialog, ft.BottomSheet)
    assert "Reservation found" in texts(page.dialog)


@then("Escale shows the import confirmation listing its reservations")
def lists(world: dict[str, Any]) -> None:
    page: FakePage = world["page"]
    assert "2 reservations found" in texts(page.dialog)


# --- details ---


def desktop_entry() -> configparser.SectionProxy:
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.optionxform = str  # type: ignore[assignment,method-assign]
    parser.read(PACKAGING / f"{APP_ID}.desktop", encoding="utf-8")
    return parser["Desktop Entry"]


def test_the_desktop_entry_opens_one_file() -> None:
    entry = desktop_entry()
    assert entry["Type"] == "Application"
    assert entry["Exec"] == "escale %f"
    assert entry["Icon"] == APP_ID


def test_it_lists_a_mime_type_for_every_file_the_picker_offers() -> None:
    types = set(filter(None, desktop_entry()["MimeType"].split(";")))
    wanted = {
        "pdf": "application/pdf",
        "pkpass": "application/vnd.apple.pkpass",
        "ics": "text/calendar",
        "itinerary": "application/vnd.kde.itinerary",
        "html": "text/html",
        "eml": "message/rfc822",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    assert set(IMPORT_EXTENSIONS) == set(wanted)
    assert types == set(wanted.values())


def test_the_itinerary_type_is_declared_as_kde_does() -> None:
    tree = ET.parse(PACKAGING / f"{APP_ID}.xml")
    ns = {"m": "http://www.freedesktop.org/standards/shared-mime-info"}
    [kind] = tree.getroot().findall("m:mime-type", ns)
    assert kind.get("type") == "application/vnd.kde.itinerary"
    assert [g.get("pattern") for g in kind.findall("m:glob", ns)] == ["*.itinerary"]


def test_no_file_starts_as_before() -> None:
    args = parse_args([])
    assert args.file is None and not args.web


def test_a_missing_file_shows_why() -> None:
    shell, page = shell_for(FakeExtractor([]))
    asyncio.run(shell.open_file(Path("/nowhere/ticket.pdf")))
    assert "Cannot read the file" in texts(page.dialog)
