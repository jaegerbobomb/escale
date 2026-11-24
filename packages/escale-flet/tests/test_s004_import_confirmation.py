"""S004 — Import with confirmation.

The shell runs the real import service with a fake extractor (the real one is tested in
escale-core) and an in-memory store; the page is a `FakePage`.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.adapters.kitinerary_cli import ExtractorError
from escale_core.importer import Importer
from escale_core.store import InMemoryReservationStore
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, button, click, texts

DATA = Path(__file__).parents[2] / "escale-core" / "tests" / "data"
TRAIN_TICKET = DATA / "train-booking.html"
TRAIN_JSONLD: list[dict[str, Any]] = json.loads(
    (DATA / "train-booking.extracted.json").read_text(encoding="utf-8")
)

scenarios("S004.feature")


@dataclass
class World:
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    store: InMemoryReservationStore = field(default_factory=InMemoryReservationStore)
    extractor: FakeExtractor = field(default_factory=lambda: FakeExtractor([]))
    file: Path = TRAIN_TICKET
    shell: Shell | None = None

    def start(self) -> Shell:
        chosen = self.file

        async def choose_file() -> Path | None:
            return chosen

        self.shell = Shell(importer=Importer(self.extractor, self.store), choose_file=choose_file)
        self.shell.mount(cast(ft.Page, self.page))
        return self.shell

    def saved(self) -> tuple[Any, ...]:
        return asyncio.run(self.store.reservations())


@pytest.fixture
def world() -> World:
    return World()


@given("a ticket file with one train reservation")
def ticket_with_one_train(world: World) -> None:
    world.file = TRAIN_TICKET
    world.extractor = FakeExtractor(TRAIN_JSONLD)


@given("a file with no reservation")
def file_without_reservation(world: World) -> None:
    world.file = DATA / "no-reservation.pdf"
    world.extractor = FakeExtractor([])


@given("the app runs on Android")
def runs_on_android(world: World) -> None:
    world.page.platform = ft.PagePlatform.ANDROID


@when("the file is imported")
def file_is_imported(world: World) -> None:
    shell = world.start()
    asyncio.run(shell.start_import())


@when("the user confirms")
def user_confirms(world: World) -> None:
    click(button(world.page.dialog, "Add to trip"))


@when("the user cancels")
def user_cancels(world: World) -> None:
    click(button(world.page.dialog, "Cancel"))


@when('the user opens "Import a file"')
def user_opens_import(world: World) -> None:
    shell = world.start()
    asyncio.run(shell.start_import())


@then("the reservation is saved")
def reservation_saved(world: World) -> None:
    assert len(world.saved()) == 1
    assert world.saved()[0].type == "TrainReservation"
    assert world.page.dialog is None


@then("no reservation is saved")
def nothing_saved(world: World) -> None:
    assert world.saved() == ()
    assert world.page.dialog is None


@then('the sheet offers "Add manually"')
def offers_manual_entry(world: World) -> None:
    assert isinstance(world.page.dialog, ft.BottomSheet)
    assert button(world.page.dialog, "Add manually") is not None
    assert world.saved() == ()


@then("the app explains that tickets are read on Linux and arrive through the sync")
def explains_phone_import(world: World) -> None:
    shown = " ".join(texts(world.page.dialog))
    assert "Linux" in shown
    assert "sync" in shown
    assert world.extractor.calls == []


# --- details the scenarios do not spell out ---


def test_the_sheet_shows_what_was_found_before_anything_is_saved() -> None:
    world = World(extractor=FakeExtractor(TRAIN_JSONLD))
    asyncio.run(world.start().start_import())
    shown = texts(world.page.dialog)
    assert "Reservation found" in shown
    assert "IC 123" in shown
    assert "Lyon Part-Dieu → Paris Gare de Lyon" in shown
    assert "Sun 14 Mar 2027 · 08:04" in shown
    assert "Jane Doe" in shown
    assert "New trip" in shown
    assert world.saved() == ()


def test_add_manually_is_disabled_until_manual_entry_exists() -> None:
    world = World(file=DATA / "no-reservation.pdf")
    asyncio.run(world.start().start_import())
    assert button(world.page.dialog, "Add manually").disabled


def test_extractor_error_is_shown_with_manual_entry() -> None:
    world = World(extractor=FakeExtractor(ExtractorError("boom")))
    asyncio.run(world.start().start_import())
    shown = " ".join(texts(world.page.dialog))
    assert "could not be read" in shown
    assert "boom" in shown
    assert button(world.page.dialog, "Add manually") is not None


def test_choosing_no_file_does_nothing() -> None:
    world = World(extractor=FakeExtractor(TRAIN_JSONLD))
    shell = world.start()

    async def no_file() -> Path | None:
        return None

    shell.choose_file = no_file
    asyncio.run(shell.start_import())
    assert world.page.dialog is None
    assert world.extractor.calls == []


def test_import_entry_and_add_button_start_an_import() -> None:
    world = World(extractor=FakeExtractor(TRAIN_JSONLD))
    shell = world.start()
    click(shell.add_button.controls[0])
    assert isinstance(world.page.dialog, ft.BottomSheet)
