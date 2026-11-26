"""S061 — Detail and editor follow the GNOME HIG (ADR-0008)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, cast

import flet as ft
import pytest
from pytest_bdd import given, scenarios, then, when

from escale_core.extraction import Document
from escale_core.importer import reservation_from_jsonld
from escale_core.store import InMemoryReservationStore
from escale_flet.demo import FLIGHT, LONDON_TRIP_FULL
from escale_flet.shell import Shell
from escale_flet.testing import FakePage, action, tagged, texts, walk

scenarios("S061.feature")

LEAVES = datetime.fromisoformat(LONDON_TRIP_FULL[0]["reservationFor"]["departureTime"])


def run(handler: Any) -> None:
    outcome = handler(None)
    if asyncio.iscoroutine(outcome):
        asyncio.run(outcome)


@dataclass
class World:
    page: FakePage = field(default_factory=lambda: FakePage(width=1000))
    store: InMemoryReservationStore = field(default_factory=InMemoryReservationStore)
    shell: Shell | None = None

    def open(self, elements: list[dict[str, Any]], ref: str, now: datetime) -> Shell:
        found = [reservation_from_jsonld(e, ("d",)) for e in elements]
        asyncio.run(
            self.store.add(Document("d", "t.pdf", "application/pdf"), [r for r in found if r])
        )
        self.shell = Shell(store=self.store, clock=lambda: now)
        self.shell.mount(cast(ft.Page, self.page))
        asyncio.run(self.shell.refresh())
        run(tagged(self.shell.body, "segment", ref).on_click)
        return self.shell

    def edit(self) -> None:
        assert self.page.appbar is not None
        run(tagged(self.page.appbar.actions, "edit").on_click)


@pytest.fixture
def world() -> World:
    return World()


@given("a segment's detail open in a window 1000 px wide")
def train_detail(world: World) -> None:
    world.open(LONDON_TRIP_FULL, "ESC-T1", LEAVES - timedelta(minutes=40))


@given("a stay's detail")
def stay_detail(world: World) -> None:
    world.open(LONDON_TRIP_FULL, "ESC-H1", LEAVES - timedelta(minutes=40))


@given("the stay editor with the check-out changed to 12:00")
def editor_changed(world: World) -> None:
    stay_detail(world)
    world.edit()
    check_out = tagged(world.page.dialog, "field", "check_out_time")
    check_out.value = "12:00"
    run(check_out.on_change)


@given("a flight's detail with a ticket")
def flight_detail(world: World) -> None:
    leaves = datetime.fromisoformat(FLIGHT["reservationFor"]["departureTime"])
    world.open([FLIGHT], "ESC-F718", leaves - timedelta(hours=2))


@when('the user clicks "Edit" in the header bar')
def click_edit(world: World) -> None:
    world.edit()


@when("the user presses Return in a field")
def press_return(world: World) -> None:
    run(tagged(world.page.dialog, "field", "check_out_time").on_submit)


@then("the header bar starts with a back button named after the trip")
def back_in_header_bar(world: World) -> None:
    assert world.page.appbar is not None
    back = world.page.appbar.leading
    assert back is not None and back.data == {"back": True}
    assert texts(back) == ["London"]
    assert back.tooltip


@then("the content has no back button")
def no_back_in_content(world: World) -> None:
    assert world.shell is not None
    assert not [
        c for c in walk(world.shell.body) if isinstance(c.data, dict) and c.data.get("back")
    ]


@then('the editor opens as a dialog with "Cancel" before "Save"')
def editor_dialog(world: World) -> None:
    dialog = world.page.dialog
    assert isinstance(dialog, ft.AlertDialog)
    labels = [
        c.content for c in walk(dialog.title) if isinstance(c, ft.TextButton | ft.FilledButton)
    ]
    assert labels == ["Cancel", "Save"]
    assert "Edit Stay" in texts(dialog.title)


@then("the dialog closes and the detail shows check-out at 12:00")
def saved(world: World) -> None:
    assert world.page.dialog is None
    assert world.shell is not None
    assert texts(tagged(world.shell.body, "moment", "Check-out"))[1] == "12:00"


@then('"Show Ticket" is the only suggested button')
def one_suggested(world: World) -> None:
    assert world.shell is not None
    suggested = [c for c in walk(world.shell.body) if type(c) is ft.FilledButton]
    assert [c.content for c in suggested] == ["Show Ticket"]


@then('"Share flight" is a row')
def share_is_a_row(world: World) -> None:
    assert world.shell is not None
    assert action(world.shell.body, "Share flight").on_click is not None


# --- details ---


def test_header_bar_in_a_detail_has_edit_but_no_add(world: World) -> None:
    stay_detail(world)
    assert world.page.appbar is not None
    actions = world.page.appbar.actions or []
    assert tagged(actions, "edit").tooltip == "Edit"
    shell = world.shell
    assert shell is not None
    assert shell.add_button not in actions and shell.add_menu_compact not in actions


def test_no_edit_for_a_train(world: World) -> None:
    train_detail(world)
    assert world.page.appbar is not None
    with pytest.raises(LookupError):
        tagged(world.page.appbar.actions, "edit")


def test_narrow_header_bar_shows_the_booking_title(world: World) -> None:
    world.page = FakePage(width=500)
    stay_detail(world)
    assert world.page.appbar is not None
    assert texts(world.page.appbar.title) == ["The Hoxton, Holborn"]


def test_escape_cancels_the_editor(world: World) -> None:
    stay_detail(world)
    world.edit()
    dialog = world.page.dialog
    assert isinstance(dialog, ft.AlertDialog)
    run(dialog.on_dismiss)
    assert world.shell is not None and not world.shell.editing


def test_phone_editor_is_a_bottom_sheet(world: World) -> None:
    world.page = FakePage(width=380)
    stay_detail(world)
    world.edit()
    sheet = world.page.dialog
    assert isinstance(sheet, ft.BottomSheet) and sheet.show_drag_handle
    assert [c.content for c in walk(sheet) if isinstance(c, ft.TextButton | ft.FilledButton)][
        :2
    ] == [
        "Cancel",
        "Save",
    ]


def test_medium_editor_is_a_floating_dialog(world: World) -> None:
    world.page = FakePage(width=500)
    stay_detail(world)
    world.edit()
    assert isinstance(world.page.dialog, ft.AlertDialog)


def test_editor_fields_are_entry_rows(world: World) -> None:
    stay_detail(world)
    world.edit()
    name = tagged(world.page.dialog, "field", "name")
    assert isinstance(name.border, ft.NoInputBorder)


def test_resizing_to_a_phone_keeps_what_was_typed(world: World) -> None:
    stay_detail(world)
    world.edit()
    name = tagged(world.page.dialog, "field", "name")
    name.value = "Typed name"
    run(name.on_change)
    world.page.resize(380)
    sheet = world.page.dialog
    assert isinstance(sheet, ft.BottomSheet)
    assert tagged(sheet, "field", "name").value == "Typed name"
    assert len(world.page.dialogs) == 1


def test_main_actions_at_the_start_of_the_header_bar() -> None:
    world = World()
    train_detail(world)
    shell = world.shell
    assert shell is not None
    run(world.page.appbar.leading.on_click)  # type: ignore[union-attr]  # back to the timeline
    assert world.page.appbar is not None
    assert world.page.appbar.leading is shell.add_button
    main, _, menu = shell.add_button.controls
    assert isinstance(main, ft.TextButton) and isinstance(menu, ft.PopupMenuButton)
    actions = world.page.appbar.actions or []
    assert not [c for c in walk(actions) if type(c) in (ft.FilledButton, ft.FilledTonalButton)]


def test_narrow_detail_does_not_repeat_the_title(world: World) -> None:
    world.page = FakePage(width=500)
    train_detail(world)
    assert world.shell is not None
    assert "IC 9014" not in texts(world.shell.body)
    assert texts(world.page.appbar.title) == ["IC 9014"]  # type: ignore[union-attr]
