"""Adaptive shell: three top-level views, tabs placed for the window width (ADR-0007).

At 550 logical px and above the tabs are a view switcher in the header; below, they
move to a bottom navigation bar. The shell reacts to resizing without a restart and
keeps the selected tab across layouts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum

import flet as ft

from escale_flet.theme import DARK_THEME, FONTS, LIGHT_THEME

NARROW_BELOW = 550
"""Window width (logical px) under which the tabs move to a bottom bar (ADR-0007)."""


class Tab(StrEnum):
    CURRENT = "current"
    TRIPS = "trips"
    STATISTICS = "statistics"


class Layout(Enum):
    WIDE = "wide"
    NARROW = "narrow"


@dataclass(frozen=True)
class TabSpec:
    tab: Tab
    label: str
    icon: ft.IconData
    selected_icon: ft.IconData
    empty_title: str
    empty_text: str


TABS: tuple[TabSpec, ...] = (
    TabSpec(
        Tab.CURRENT,
        "Current",
        ft.Icons.LUGGAGE_OUTLINED,
        ft.Icons.LUGGAGE,
        "No current trip",
        "Import a ticket to start one.",
    ),
    TabSpec(
        Tab.TRIPS,
        "My trips",
        ft.Icons.MAP_OUTLINED,
        ft.Icons.MAP,
        "No trips yet",
        "Your past and upcoming trips will be listed here.",
    ),
    TabSpec(
        Tab.STATISTICS,
        "Statistics",
        ft.Icons.INSIGHTS_OUTLINED,
        ft.Icons.INSIGHTS,
        "No statistics yet",
        "Distances, countries and nights away, once you have travelled.",
    ),
)

ADD_MENU_ENTRIES: tuple[str, ...] = ("Import a ticket…", "New trip…", "Search a train…")
"""Entries of the "Add" menu, disabled until the stories that implement them land."""


def layout_for(width: float | None) -> Layout:
    """Layout for a window ``width``; an unknown width is treated as wide."""
    if width is not None and width < NARROW_BELOW:
        return Layout.NARROW
    return Layout.WIDE


def tab_for_route(route: str | None) -> Tab:
    """Tab named by a route such as ``/trips``; anything else opens "Current"."""
    name = (route or "").strip("/").split("/")[0]
    return Tab(name) if name in {tab.value for tab in Tab} else Tab.CURRENT


def _spec(tab: Tab) -> TabSpec:
    return next(spec for spec in TABS if spec.tab == tab)


def _empty_view(spec: TabSpec) -> ft.Control:
    """A placeholder in the style of libadwaita's status page."""
    return ft.Column(
        [
            ft.Icon(spec.icon, size=72, opacity=0.4),
            ft.Text(spec.empty_title, theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
            ft.Text(spec.empty_text, opacity=0.7, text_align=ft.TextAlign.CENTER),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=12,
        tight=True,
    )


def _add_menu_items() -> list[ft.PopupMenuItem]:
    return [ft.PopupMenuItem(content=ft.Text(entry), disabled=True) for entry in ADD_MENU_ENTRIES]


class Shell:
    """The window's top-level structure; ``mount`` attaches it to a Flet page."""

    def __init__(self) -> None:
        self.selected = Tab.CURRENT
        self.layout = Layout.WIDE
        self._page: ft.Page | None = None

        self.switcher = ft.SegmentedButton(
            segments=[
                ft.Segment(value=spec.tab.value, label=ft.Text(spec.label), icon=ft.Icon(spec.icon))
                for spec in TABS
            ],
            selected=[self.selected.value],
            allow_empty_selection=False,
            allow_multiple_selection=False,
            show_selected_icon=False,
            on_change=self._on_switcher_change,
        )
        self.bottom_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationBarDestination(
                    icon=spec.icon, selected_icon=spec.selected_icon, label=spec.label
                )
                for spec in TABS
            ],
            selected_index=0,
            on_change=self._on_bottom_bar_change,
        )
        # libadwaita's split button: the main action and its menu side by side.
        self.add_button = ft.Row(
            [
                ft.FilledButton(
                    "Add",
                    icon=ft.Icons.ADD,
                    disabled=True,
                    tooltip="Coming with ticket import",
                ),
                ft.PopupMenuButton(
                    icon=ft.Icons.ARROW_DROP_DOWN, tooltip="Add…", items=_add_menu_items()
                ),
            ],
            spacing=0,
        )
        self.add_menu_compact = ft.PopupMenuButton(
            icon=ft.Icons.ADD, tooltip="Add…", items=_add_menu_items()
        )
        self.appbar = ft.AppBar(center_title=True, actions_padding=ft.Padding.only(right=8))
        self.body = ft.Container(
            content=_empty_view(_spec(self.selected)),
            expand=True,
            alignment=ft.Alignment.CENTER,
            padding=ft.Padding.all(24),
        )

    # --- attaching to a page ---

    def mount(self, page: ft.Page) -> None:
        page.title = "Escale"
        page.fonts = FONTS
        page.theme = LIGHT_THEME
        page.dark_theme = DARK_THEME
        page.theme_mode = ft.ThemeMode.SYSTEM
        page.padding = 0
        page.appbar = self.appbar
        page.on_resize = self._on_resize
        self._page = page
        self.selected = tab_for_route(page.route)
        self.layout = layout_for(page.width)
        self._apply()
        page.add(self.body)

    # --- state changes ---

    def resize(self, width: float | None) -> None:
        layout = layout_for(width)
        if layout != self.layout:
            self.layout = layout
            self._apply()
            self._update()

    def select(self, tab: Tab) -> None:
        if tab != self.selected:
            self.selected = tab
            self._apply()
            self._update()

    # --- rendering ---

    def _apply(self) -> None:
        index = [spec.tab for spec in TABS].index(self.selected)
        self.switcher.selected = [self.selected.value]
        self.bottom_bar.selected_index = index
        self.body.content = _empty_view(_spec(self.selected))
        if self.layout == Layout.WIDE:
            self.appbar.title = self.switcher
            self.appbar.actions = [self.add_button]
            navigation_bar = None
        else:
            self.appbar.title = ft.Text(_spec(self.selected).label)
            self.appbar.actions = [self.add_menu_compact]
            navigation_bar = self.bottom_bar
        if self._page is not None:
            self._page.navigation_bar = navigation_bar

    def _update(self) -> None:
        if self._page is not None:
            self._page.update()

    # --- event handlers ---

    def _on_resize(self, e: ft.PageResizeEvent) -> None:
        self.resize(e.width)

    def _on_switcher_change(self, e: ft.Event[ft.SegmentedButton]) -> None:
        if e.control.selected:
            self.select(Tab(e.control.selected[0]))

    def _on_bottom_bar_change(self, e: ft.Event[ft.NavigationBar]) -> None:
        self.select(TABS[e.control.selected_index or 0].tab)
