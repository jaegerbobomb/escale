"""Adaptive shell: three top-level views, tabs placed for the window width (ADR-0007).

At 550 logical px and above the tabs are a view switcher in the header; below, they
move to a bottom navigation bar. The shell reacts to resizing without a restart and
keeps the selected tab across layouts.
"""

from __future__ import annotations

import tempfile
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

import flet as ft

from escale_core.adapters.kitinerary_cli import KitineraryCli
from escale_core.extraction import ExtractedReservation
from escale_core.importer import Importer
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.trips import Trip, active_trip, group
from escale_flet.import_sheet import confirmation_sheet, phone_sheet
from escale_flet.theme import DARK_THEME, FONTS, LIGHT_THEME
from escale_flet.ticket_view import MAX_WIDTH as TICKET_WIDTH
from escale_flet.ticket_view import ticket_view
from escale_flet.timeline import MAX_WIDTH, trip_view

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

IMPORT_ENTRY = "Import a file…"
ADD_MENU_ENTRIES: tuple[str, ...] = (
    "Search a train…",
    IMPORT_ENTRY,
    "Scan or paste…",
    "New trip…",
    "New outing…",
    "Add manually…",
)
"""The mockup's "Add" menu; entries other than import wait for their stories."""

SPLIT_RADIUS = 7
"""libadwaita's standard control radius, used by the "Add" split button."""

IMPORT_EXTENSIONS = ["pdf", "pkpass", "ics", "itinerary", "html", "eml", "png", "jpg", "jpeg"]
"""What kitinerary-extractor reads (ADR-0003)."""

PHONES = {ft.PagePlatform.ANDROID, ft.PagePlatform.IOS, ft.PagePlatform.ANDROID_TV}

FileChooser = Callable[[], Awaitable[Path | None]]


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


def _add_menu_items(on_import: Callable[[Any], Awaitable[None]]) -> list[ft.PopupMenuItem]:
    return [
        ft.PopupMenuItem(content=ft.Text(entry), on_click=on_import)
        if entry == IMPORT_ENTRY
        else ft.PopupMenuItem(content=ft.Text(entry), disabled=True)
        for entry in ADD_MENU_ENTRIES
    ]


class Shell:
    """The window's top-level structure; ``mount`` attaches it to a Flet page."""

    def __init__(
        self,
        importer: Importer | None = None,
        choose_file: FileChooser | None = None,
        store: ReservationStore | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if importer is None:
            importer = Importer(KitineraryCli(), store or InMemoryReservationStore())
        self.importer = importer
        self.store: ReservationStore = store or importer.store
        self.clock: Callable[[], datetime] = clock or (lambda: datetime.now().astimezone())
        self.trip: Trip | None = None
        self.ticket: ExtractedReservation | None = None
        self.choose_file: FileChooser = choose_file or self._pick_file
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
        # libadwaita's AdwSplitButton (.suggested-action): the main action and its menu as
        # two joined buttons, standard 7 px radius, no shadow, a 1 px separator between.
        self.add_button = ft.Row(
            [
                ft.FilledButton(
                    "Add",
                    icon=ft.Icons.ADD,
                    tooltip="Import a file",
                    on_click=self._on_import,
                    height=36,
                    style=ft.ButtonStyle(
                        elevation=0,
                        shape=ft.RoundedRectangleBorder(
                            radius=ft.BorderRadius.only(
                                top_left=SPLIT_RADIUS, bottom_left=SPLIT_RADIUS
                            )
                        ),
                    ),
                ),
                ft.Container(
                    width=1,
                    height=36,
                    bgcolor=ft.Colors.with_opacity(0.35, ft.Colors.ON_PRIMARY),
                ),
                ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Icon(ft.Icons.ARROW_DROP_DOWN, color=ft.Colors.ON_PRIMARY),
                        bgcolor=ft.Colors.PRIMARY,
                        height=36,
                        padding=ft.Padding.symmetric(horizontal=6),
                        border_radius=ft.BorderRadius.only(
                            top_right=SPLIT_RADIUS, bottom_right=SPLIT_RADIUS
                        ),
                    ),
                    tooltip="Add…",
                    items=_add_menu_items(self._on_import),
                ),
            ],
            spacing=0,
        )
        self.add_menu_compact = ft.PopupMenuButton(
            icon=ft.Icons.ADD, tooltip="Add…", items=_add_menu_items(self._on_import)
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

    async def refresh(self) -> None:
        """Reload the stored reservations and show the active trip in "Current"."""
        trips = group(await self.store.reservations())
        self.trip = active_trip(trips, self.clock())
        self._apply()
        self._update()

    async def show_ticket(self, reservation: ExtractedReservation) -> None:
        """The ticket full screen, screen brightness up while it is shown (S015)."""
        self.ticket = reservation
        await self._brightness(full=True)
        self._apply()
        self._update()

    async def close_ticket(self) -> None:
        self.ticket = None
        await self._brightness(full=False)
        self._apply()
        self._update()

    async def _brightness(self, full: bool) -> None:
        if not isinstance(self._page, ft.Page):
            return  # a test page, or not mounted
        try:
            service = ft.ScreenBrightness()
            if full:
                await service.set_application_screen_brightness(1.0)
            else:
                await service.reset_application_screen_brightness()  # type: ignore[no-untyped-call]
        except Exception:
            return

    def _open_document(
        self, reservation: ExtractedReservation
    ) -> Callable[[Any], Awaitable[None]] | None:
        locate = getattr(self.store, "document_path", None)
        if locate is None or self._page is None:
            return None
        for document_id in reservation.subject_of:
            path = locate(document_id)
            if path is not None:
                url = path.as_uri()

                async def open_it(_: Any, url: str = url) -> None:
                    await ft.UrlLauncher().launch_url(url)

                return open_it
        return None

    async def start_import(self) -> None:
        """Choose a file, show what it holds, save it only if the user confirms (S004)."""
        page = self._page
        if page is None:
            return
        if page.platform in PHONES and not page.web:
            page.show_dialog(phone_sheet(self._close_sheet))
            return
        path = await self.choose_file()
        if path is None:
            return
        result = await self.importer.preview(path)

        async def confirm(_: Any) -> None:
            await self.importer.confirm(result)
            await self.refresh()
            self._close_sheet(None)

        page.show_dialog(confirmation_sheet(result, confirm, self._close_sheet))

    def _close_sheet(self, _: Any) -> None:
        if self._page is not None:
            self._page.pop_dialog()

    async def _pick_file(self) -> Path | None:
        """The system file chooser; in a browser the file is copied to a temporary folder."""
        web = self._page is not None and self._page.web
        files = await ft.FilePicker().pick_files(
            dialog_title="Import a file", allowed_extensions=IMPORT_EXTENSIONS, with_data=web
        )
        if not files:
            return None
        picked = files[0]
        if picked.path:
            return Path(picked.path)
        if picked.bytes is None:
            return None
        target = Path(tempfile.mkdtemp(prefix="escale-import-")) / Path(picked.name).name
        target.write_bytes(picked.bytes)
        return target

    # --- rendering ---

    def _apply(self) -> None:
        index = [spec.tab for spec in TABS].index(self.selected)
        self.switcher.selected = [self.selected.value]
        self.bottom_bar.selected_index = index
        if self.ticket is not None:
            self.body.content = ft.Container(
                ticket_view(self.ticket, self._open_document(self.ticket)),
                max_width=TICKET_WIDTH,
                expand=True,
            )
            self.body.alignment = ft.Alignment.TOP_CENTER
            self.appbar.leading = ft.IconButton(
                ft.Icons.ARROW_BACK, tooltip="Back", on_click=self._on_close_ticket
            )
            self.appbar.title = ft.Text("Ticket")
            self.appbar.actions = []
            if self._page is not None:
                self._page.navigation_bar = None
            return
        self.appbar.leading = None
        if self.selected == Tab.CURRENT and self.trip is not None:
            self.body.content = ft.Container(
                trip_view(self.trip, self.clock(), self._on_ticket),
                max_width=MAX_WIDTH,
                expand=True,
            )
            self.body.alignment = ft.Alignment.TOP_CENTER
        else:
            self.body.content = _empty_view(_spec(self.selected))
            self.body.alignment = ft.Alignment.CENTER
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

    def _on_ticket(self, reservation: ExtractedReservation) -> None:
        if self._page is not None and isinstance(self._page, ft.Page):
            self._page.run_task(self.show_ticket, reservation)
        else:
            self.ticket = reservation
            self._apply()

    async def _on_close_ticket(self, _: Any) -> None:
        await self.close_ticket()

    async def _on_import(self, _: Any) -> None:
        await self.start_import()

    def _on_resize(self, e: ft.PageResizeEvent) -> None:
        self.resize(e.width)

    def _on_switcher_change(self, e: ft.Event[ft.SegmentedButton]) -> None:
        if e.control.selected:
            self.select(Tab(e.control.selected[0]))

    def _on_bottom_bar_change(self, e: ft.Event[ft.NavigationBar]) -> None:
        self.select(TABS[e.control.selected_index or 0].tab)
