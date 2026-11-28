"""S064 — Keep the file of a failed import with the booking then added by hand."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.adapters.fake_extractor import FakeExtractor
from escale_core.importer import Importer
from escale_core.store import InMemoryReservationStore
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, button, click, tagged, texts

scenarios("S064.feature")

NOW = datetime.fromisoformat("2027-06-01T09:00:00+02:00")


@pytest.fixture(autouse=True)
def paris(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("TZ", "Europe/Paris")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


class World:
    def __init__(self, folder: Path, width: int = 1000) -> None:
        self.page = FakePage(width=width)
        self.store = InMemoryReservationStore()
        self.file = folder / "coach.pdf"
        self.file.write_bytes(b"%PDF-1.4 a coach ticket nobody can read")

        async def choose_file() -> Path | None:
            return self.file

        self.shell = Shell(
            importer=Importer(FakeExtractor([]), self.store),
            store=self.store,
            choose_file=choose_file,
            clock=lambda: NOW,
        )
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())

    def failed_import(self) -> None:
        asyncio.run(self.shell.start_import())
        assert "Nothing recognised" in texts(self.page.dialog)

    def menu_entry(self, label: str) -> Any:
        [menu] = [c for c in self.shell.add_button.controls if isinstance(c, ft.PopupMenuButton)]
        [item] = [i for i in menu.items if cast(ft.Text, i.content).value == label]
        return item

    def choose(self, kind: str) -> None:
        click(tagged(self.page.dialog, "manual_kind", kind))

    def fill(self, **values: str) -> None:
        for name, value in values.items():
            field = tagged(self.page.dialog, "field", name)
            field.value = value
            field.on_change(None)

    def fill_bus(self) -> None:
        self.fill(
            departure_name="Paris Bercy",
            departure_date="2027-07-08",
            departure_time="08:00",
            arrival_name="Lyon Perrache",
        )

    def saved(self) -> tuple[Any, ...]:
        return asyncio.run(self.store.reservations())

    def documents(self) -> tuple[Any, ...]:
        return asyncio.run(self.store.documents())


@pytest.fixture
def world(tmp_path: Path) -> World:
    return World(tmp_path)


@given('a file "coach.pdf" with no reservation was imported')
def imported(world: World) -> None:
    world.failed_import()


@given("a file with no reservation was imported and closed")
def imported_and_closed(world: World) -> None:
    world.failed_import()
    click(button(world.page.dialog, "Cancel"))
    assert world.page.dialog is None


@when('the user chooses "Add manually", then "Bus", fills the trip and saves')
def add_bus(world: World) -> None:
    click(button(world.page.dialog, "Add manually"))
    world.choose("bus")
    world.fill_bus()
    click(button(world.page.dialog, "Save"))


@when('the user chooses "Add manually", then "Bus", and cancels')
def add_and_cancel(world: World) -> None:
    click(button(world.page.dialog, "Add manually"))
    world.choose("bus")
    world.fill_bus()
    click(button(world.page.dialog, "Cancel"))


@when('the user adds a stay from "Add → Add manually…"')
def add_stay_from_menu(world: World) -> None:
    click(world.menu_entry("Add manually…"))
    world.choose("stay")
    world.fill(
        name="Hôtel du Nord",
        check_in_date="2027-07-08",
        check_in_time="15:00",
        check_out_date="2027-07-10",
        check_out_time="11:00",
    )
    click(button(world.page.dialog, "Save"))


@then('the bus is saved with the document "coach.pdf"')
def saved_with_document(world: World) -> None:
    [bus] = world.saved()
    [document] = world.documents()
    assert bus.type == "BusReservation"
    assert document.name == "coach.pdf"
    assert bus.subject_of == (document.id,)
    assert world.store.document_path(document.id) == world.file


@then("its ticket opens the original document")
def ticket_opens_it(world: World) -> None:
    opened: list[str] = []

    async def launch(url: str) -> None:
        opened.append(url)

    world.shell.launch = launch
    assert world.shell.detail is not None
    assert "Show Ticket" in texts(world.shell.body)
    asyncio.run(world.shell.show_ticket(world.shell.detail))
    document = button(world.shell.body, "Open the original document")
    assert not document.disabled
    asyncio.run(document.on_click(None))
    assert opened == [world.file.as_uri()]


@then("no booking and no document are saved")
def nothing_saved(world: World) -> None:
    assert world.saved() == () and world.documents() == ()
    assert world.page.dialog is None


@then("the stay is saved with no document")
def stay_without_document(world: World) -> None:
    [stay] = world.saved()
    assert stay.subject_of == () and world.documents() == ()


# --- details ---


def test_the_editor_names_the_file_it_attaches(world: World) -> None:
    world.failed_import()
    click(button(world.page.dialog, "Add manually"))
    world.choose("stay")
    assert "Attached: coach.pdf" in texts(world.page.dialog)


def test_the_file_stays_when_the_editor_changes_presentation(world: World) -> None:
    world.failed_import()
    click(button(world.page.dialog, "Add manually"))
    world.choose("bus")
    world.page.width = 380
    world.shell.resize(380)
    assert isinstance(world.page.dialog, ft.BottomSheet)
    assert "Attached: coach.pdf" in texts(world.page.dialog)


@pytest.mark.parametrize("how", ["chooser", "escape"])
def test_leaving_the_chooser_forgets_the_file(world: World, how: str) -> None:
    world.failed_import()
    click(button(world.page.dialog, "Add manually"))
    if how == "chooser":
        click(button(world.page.dialog, "Cancel"))
    else:  # Esc or a click outside
        chooser: Any = world.page.dialog
        world.page.pop_dialog()
        chooser.on_dismiss(None)
    click(world.menu_entry("Add manually…"))
    world.choose("stay")
    assert not any(t.startswith("Attached:") for t in texts(world.page.dialog))


def test_dismissing_the_editor_forgets_the_file(world: World) -> None:
    world.failed_import()
    click(button(world.page.dialog, "Add manually"))
    world.choose("bus")
    editor: Any = world.page.dialog
    world.page.pop_dialog()
    editor.on_dismiss(None)
    click(world.menu_entry("Add manually…"))
    world.choose("bus")
    assert not any(t.startswith("Attached:") for t in texts(world.page.dialog))
