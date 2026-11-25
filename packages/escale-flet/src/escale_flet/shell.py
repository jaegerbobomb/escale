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
from escale_core.flights import follow_link
from escale_core.importer import Importer
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.trips import Trip, active_trip, group
from escale_flet.detail_view import detail_view
from escale_flet.import_sheet import confirmation_sheet, headline, phone_sheet
from escale_flet.theme import DARK_THEME, FONTS, LIGHT_THEME
from escale_flet.ticket_view import MAX_WIDTH as TICKET_WIDTH
from escale_flet.ticket_view import ticket_view
from escale_flet.timeline import (
    MAX_WIDTH,
    has_ticket,
    jump_entries,
    jump_panel,
    next_segment,
    segment_ref,
    trip_view,
)

NARROW_BELOW = 550
"""Window width (logical px) under which the tabs move to a bottom bar (ADR-0007)."""


COMPACT_BELOW = 400
"""Window width under which the jump index is a bottom sheet and a detail a pushed page."""


def segment_ref_title(reservation: ExtractedReservation) -> str:
    from escale_flet.timeline import _title

    return _title(reservation)


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
Sharer = Callable[[str], Awaitable[str | None]]
"""Shares a text; returns a message to confirm it (``None``: the system showed its own)."""


def shares_with_sheet(platform: ft.PagePlatform | None) -> bool:
    """Phones have a share sheet; elsewhere Escale copies the text instead (S016)."""
    return platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)


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
        share: Sharer | None = None,
    ) -> None:
        if importer is None:
            importer = Importer(KitineraryCli(), store or InMemoryReservationStore())
        self.importer = importer
        self.store: ReservationStore = store or importer.store
        self.clock: Callable[[], datetime] = clock or (lambda: datetime.now().astimezone())
        self.trip: Trip | None = None
        self.ticket: ExtractedReservation | None = None
        self.detail: ExtractedReservation | None = None
        self.highlight: str | None = None
        self.scroll_target: str | None = None
        self.width: float | None = None
        self._timeline: ft.Column | None = None
        self.choose_file: FileChooser = choose_file or self._pick_file
        self.share: Sharer = share or self._share_text
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
        self.width = page.width
        self._apply()
        page.add(self.body)

    # --- state changes ---

    def resize(self, width: float | None) -> None:
        was_compact = self._compact()
        self.width = width
        layout = layout_for(width)
        if layout != self.layout or self._compact() != was_compact:
            self.layout = layout
            self._apply()
            self._update()

    def _compact(self) -> bool:
        """Under 400 px: the index is a bottom sheet, the detail a pushed page (ADR-0007)."""
        return self.width is not None and self.width < COMPACT_BELOW

    # --- jump index and segment detail (S011) ---

    async def jump(self, ref: str) -> None:
        """Scroll the timeline to a segment and highlight it, without changing the view."""
        self.highlight = ref
        self._apply()
        self._update()
        await self._scroll_to(ref)

    async def _scroll_to(self, ref: str) -> None:
        self.scroll_target = ref
        if isinstance(self._page, ft.Page) and self._timeline is not None:
            await self._timeline.scroll_to(scroll_key=ref, duration=300)

    def open_detail(self, reservation: ExtractedReservation) -> None:
        self.detail = reservation
        self.highlight = segment_ref(reservation)
        self._apply()
        self._update()

    async def close_detail(self) -> None:
        ref = segment_ref(self.detail) if self.detail is not None else None
        self.detail = None
        if ref is None:
            self._apply()
            self._update()
            return
        await self.jump(ref)

    async def _on_jump(self, reservation: ExtractedReservation) -> None:
        await self.jump(segment_ref(reservation))

    def _open_jump_sheet(self, _: Any) -> None:
        if self._page is None or self.trip is None:
            return

        async def jump_from_sheet(reservation: ExtractedReservation) -> None:
            if self._page is not None:
                self._page.pop_dialog()
            await self.jump(segment_ref(reservation))

        self._page.show_dialog(
            ft.BottomSheet(
                ft.Container(
                    ft.Column(
                        [
                            ft.Text("Jump to", size=13, color=ft.Colors.ON_SURFACE_VARIANT),
                            *jump_entries(self.trip, jump_from_sheet),
                        ],
                        tight=True,
                        spacing=2,
                    ),
                    padding=16,
                ),
                show_drag_handle=True,
            )
        )

    def _jump_control(self) -> ft.Control | None:
        """Medium window: a "Jump to…" menu; narrow: a button opening a bottom sheet."""
        if self.trip is None or self.layout == Layout.WIDE:
            return None
        if self._compact():
            return ft.IconButton(
                ft.Icons.FORMAT_LIST_BULLETED,
                tooltip="Jump to…",
                on_click=self._open_jump_sheet,
                data={"jump_sheet": True},
            )
        trip = self.trip
        return ft.PopupMenuButton(
            icon=ft.Icons.FORMAT_LIST_BULLETED,
            tooltip="Jump to…",
            items=[
                ft.PopupMenuItem(
                    content=ft.Text(text),
                    on_click=lambda _, r=r: self._jump_soon(r),
                )
                for r, text in ((r, segment_ref_title(r)) for r in trip.reservations)
            ],
        )

    def _jump_soon(self, reservation: ExtractedReservation) -> Any:
        return self.jump(segment_ref(reservation))

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

    def _share_flight(
        self, reservation: ExtractedReservation
    ) -> Callable[[Any], Awaitable[None]] | None:
        """ "Share flight": a Flightradar24 link, when the callsign is known (S016)."""
        link = follow_link(reservation)
        if link is None:
            return None
        text = f"Follow flight {headline(reservation)}: {link}"

        async def share_it(_: Any) -> None:
            message = await self.share(text)
            if message and self._page is not None:
                self._page.show_dialog(ft.SnackBar(ft.Text(message)))

        return share_it

    async def _share_text(self, text: str) -> str | None:
        page = self._page
        if not isinstance(page, ft.Page):
            return None
        try:
            if shares_with_sheet(page.platform):
                await ft.Share().share_text(text, subject="Follow my flight")
                return None
            await ft.Clipboard().set(text)
        except Exception:
            return "Could not share the link"
        return "Link copied"

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
        hide_tabs = False
        if self.selected == Tab.CURRENT and self.trip is not None and self.detail is not None:
            self.body.content = ft.Container(
                detail_view(
                    self.detail,
                    self.trip.name,
                    self._on_close_detail,
                    self._ticket_handler(self.detail) if has_ticket(self.detail) else None,
                    self._open_document(self.detail),
                    self._share_flight(self.detail),
                ),
                max_width=MAX_WIDTH,
                expand=True,
            )
            self.body.alignment = ft.Alignment.TOP_CENTER
            hide_tabs = self._compact()
        elif self.selected == Tab.CURRENT and self.trip is not None:
            self._timeline = trip_view(
                self.trip,
                self.clock(),
                self._on_ticket,
                self.open_detail,
                self.highlight,
                self._jump_control(),
            )
            content: ft.Control = self._timeline
            if self.layout == Layout.WIDE:
                content = ft.Row(
                    [
                        jump_panel(self.trip, self._on_jump),
                        ft.Container(self._timeline, expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True,
                )
            self.body.content = ft.Container(content, max_width=MAX_WIDTH + 260, expand=True)
            self.body.alignment = ft.Alignment.TOP_CENTER
        else:
            self.body.content = _empty_view(_spec(self.selected))
            self.body.alignment = ft.Alignment.CENTER
        if self.layout == Layout.WIDE:
            self.appbar.title = self.switcher
            self.appbar.actions = [*self._ticket_action(wide=True), self.add_button]
            navigation_bar = None
        else:
            self.appbar.title = ft.Text(_spec(self.selected).label)
            self.appbar.actions = [*self._ticket_action(wide=False), self.add_menu_compact]
            navigation_bar = None if hide_tabs else self.bottom_bar
        if self._page is not None:
            self._page.navigation_bar = navigation_bar

    def _update(self) -> None:
        if self._page is not None:
            self._page.update()

    # --- event handlers ---

    def current_ticket(self) -> ExtractedReservation | None:
        """The next segment of the active trip, if it has a ticket to show (S021)."""
        if self.trip is None:
            return None
        upcoming = next_segment(self.trip, self.clock())
        return upcoming if upcoming is not None and has_ticket(upcoming) else None

    def _ticket_action(self, wide: bool) -> list[ft.Control]:
        """The header bar's shortcut to the current ticket, on every tab."""
        if self.current_ticket() is None:
            return []
        tooltip = "Show the current ticket"
        icon = ft.Icons.CONFIRMATION_NUMBER_OUTLINED
        if wide:
            return [
                ft.FilledTonalButton(
                    "Ticket", icon=icon, tooltip=tooltip, on_click=self._on_current_ticket
                ),
                ft.Container(width=8),
            ]
        return [ft.IconButton(icon, tooltip=tooltip, on_click=self._on_current_ticket)]

    def _on_current_ticket(self, _: Any) -> None:
        reservation = self.current_ticket()
        if reservation is not None:
            self._on_ticket(reservation)

    def _on_ticket(self, reservation: ExtractedReservation) -> None:
        if self._page is not None and isinstance(self._page, ft.Page):
            self._page.run_task(self.show_ticket, reservation)
        else:
            self.ticket = reservation
            self._apply()

    def _ticket_handler(self, reservation: ExtractedReservation) -> Callable[[Any], None]:
        def show(_: Any) -> None:
            self._on_ticket(reservation)

        return show

    async def _on_close_detail(self, _: Any) -> None:
        await self.close_detail()

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
