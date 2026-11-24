"""S002 — Adaptive shell with Adwaita theme.

The scenarios drive the shell through a stand-in for the Flet page: the same
attributes and the same resize event the real page uses, without a Flutter client.
What the page looks like is checked from screenshots (`tools/screenshots.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, cast

import flet as ft
import pytest
from escale_flet.shell import NARROW_BELOW, Layout, Shell, Tab, layout_for, tab_for_route
from escale_flet.theme import DARK, DARK_THEME, LIGHT, LIGHT_THEME, tokens
from pytest_bdd import given, parsers, scenarios, then, when

scenarios("S002.feature")


@dataclass
class FakePage:
    """The part of `ft.Page` the shell uses."""

    width: float | None = None
    route: str = "/"
    platform_brightness: ft.Brightness = ft.Brightness.LIGHT
    title: str | None = None
    fonts: dict[str, str] | None = None
    theme: ft.Theme | None = None
    dark_theme: ft.Theme | None = None
    theme_mode: ft.ThemeMode | None = None
    padding: Any = None
    appbar: ft.AppBar | None = None
    navigation_bar: ft.NavigationBar | None = None
    on_resize: Any = None
    controls: list[ft.Control] = field(default_factory=list)
    updates: int = 0

    def add(self, *controls: ft.Control) -> None:
        self.controls.extend(controls)

    def update(self) -> None:
        self.updates += 1

    def resize(self, width: float) -> None:
        self.width = width
        event = ft.PageResizeEvent(
            name="resize", control=cast(ft.Page, self), width=width, height=800
        )
        self.on_resize(event)

    def effective_theme(self) -> ft.Theme | None:
        """The theme Flutter applies for this page's mode and platform brightness."""
        dark = self.theme_mode == ft.ThemeMode.DARK or (
            self.theme_mode == ft.ThemeMode.SYSTEM
            and self.platform_brightness == ft.Brightness.DARK
        )
        return self.dark_theme if dark else self.theme


def header_tabs(page: FakePage) -> list[str]:
    title = page.appbar.title if page.appbar else None
    if not isinstance(title, ft.SegmentedButton):
        return []
    return [cast(ft.Text, segment.label).value or "" for segment in title.segments]


def header_selected(page: FakePage) -> str | None:
    title = page.appbar.title if page.appbar else None
    if isinstance(title, ft.SegmentedButton) and title.selected:
        return title.selected[0]
    return None


def bottom_tabs(page: FakePage) -> list[str]:
    if page.navigation_bar is None:
        return []
    return [destination.label or "" for destination in page.navigation_bar.destinations]


def bottom_selected(page: FakePage) -> str | None:
    bar = page.navigation_bar
    if bar is None or bar.selected_index is None:
        return None
    return bottom_tabs(page)[bar.selected_index]


LABELS = {Tab.CURRENT: "Current", Tab.TRIPS: "My trips", Tab.STATISTICS: "Statistics"}


@dataclass
class World:
    page: FakePage = field(default_factory=FakePage)
    shell: Shell = field(default_factory=Shell)
    selected_before: Tab | None = None

    def start(self) -> None:
        self.shell.mount(cast(ft.Page, self.page))


@pytest.fixture
def world() -> World:
    return World()


# --- steps ---


@given(parsers.parse("the app is open in a window {width:d} px wide"))
def app_open_at(world: World, width: int) -> None:
    world.page.width = width
    world.start()
    world.selected_before = world.shell.selected


@given("the system prefers a dark theme")
def system_prefers_dark(world: World) -> None:
    world.page.platform_brightness = ft.Brightness.DARK


@when("the app starts")
def app_starts(world: World) -> None:
    world.start()


@when(parsers.parse("the window is resized to {width:d} px wide"))
def window_resized(world: World, width: int) -> None:
    world.page.resize(width)


@then(parsers.re(r'the tabs "(?P<a>[^"]+)", "(?P<b>[^"]+)" and "(?P<c>[^"]+)" are in the header'))
def tabs_in_header(world: World, a: str, b: str, c: str) -> None:
    assert header_tabs(world.page) == [a, b, c]


@then("no bottom navigation bar is shown")
def no_bottom_bar(world: World) -> None:
    assert world.page.navigation_bar is None


@then("the tabs are in a bottom navigation bar")
def tabs_in_bottom_bar(world: World) -> None:
    assert bottom_tabs(world.page) == list(LABELS.values())
    assert header_tabs(world.page) == []


@then("the selected tab is still selected")
def selection_kept(world: World) -> None:
    assert world.selected_before is not None
    assert bottom_selected(world.page) == LABELS[world.selected_before]


@then(parsers.parse('the "{label}" tab is selected'))
def tab_selected(world: World, label: str) -> None:
    assert LABELS[world.shell.selected] == label
    assert header_selected(world.page) == world.shell.selected.value


@then("the app uses the dark variant of the theme")
def uses_dark_variant(world: World) -> None:
    assert world.page.theme_mode == ft.ThemeMode.SYSTEM
    assert world.page.effective_theme() is DARK_THEME


# --- details the scenarios do not spell out ---


@pytest.mark.parametrize(
    ("width", "layout"),
    [(None, Layout.WIDE), (1000, Layout.WIDE), (NARROW_BELOW, Layout.WIDE), (549.9, Layout.NARROW)],
)
def test_breakpoint(width: float | None, layout: Layout) -> None:
    assert layout_for(width) == layout


def test_a_tab_chosen_before_resizing_stays_selected_both_ways() -> None:
    world = World(page=FakePage(width=1000))
    world.start()
    world.shell.select(Tab.TRIPS)

    world.page.resize(500)
    assert bottom_selected(world.page) == "My trips"

    world.page.resize(800)
    assert header_selected(world.page) == Tab.TRIPS.value
    assert world.page.navigation_bar is None


def test_resizing_within_a_layout_does_not_redraw() -> None:
    world = World(page=FakePage(width=1000))
    world.start()

    world.page.resize(700)

    assert world.page.updates == 0


@pytest.mark.parametrize(
    ("route", "tab"),
    [
        ("/", Tab.CURRENT),
        ("/trips", Tab.TRIPS),
        ("/statistics/", Tab.STATISTICS),
        ("/x", Tab.CURRENT),
    ],
)
def test_initial_route_selects_a_tab(route: str, tab: Tab) -> None:
    assert tab_for_route(route) == tab


def test_light_system_theme_uses_the_light_variant() -> None:
    world = World()
    world.start()
    assert world.page.effective_theme() is LIGHT_THEME


def test_add_menu_entries_are_present_and_disabled() -> None:
    world = World(page=FakePage(width=1000))
    world.start()
    menu = world.shell.add_button.controls[1]
    assert isinstance(menu, ft.PopupMenuButton)
    assert [cast(ft.Text, item.content).value for item in menu.items] == [
        "Import a ticket…",
        "New trip…",
        "Search a train…",
    ]
    assert all(item.disabled for item in menu.items)


def test_state_colours_are_tokens_per_variant() -> None:
    assert tokens(ft.Brightness.DARK) is DARK
    assert tokens(ft.Brightness.LIGHT) is LIGHT
    assert LIGHT.outing == "#9141ac"
    assert LIGHT.accent_bg == "#3584e4"
