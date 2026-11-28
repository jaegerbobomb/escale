"""Adaptive shell: three top-level views, tabs placed for the window width (ADR-0007).

At 550 logical px and above the tabs are a view switcher in the header; below, they
move to a bottom navigation bar. The shell reacts to resizing without a restart and
keeps the selected tab across layouts.
"""

from __future__ import annotations

import tempfile
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

import flet as ft

from escale_core import flight_edit, stays, transit_edit
from escale_core.account import Account
from escale_core.adapters.kitinerary_cli import KitineraryCli
from escale_core.documents import Documents
from escale_core.extraction import ExtractedReservation
from escale_core.flights import follow_link
from escale_core.importer import Importer
from escale_core.stays import new_stay
from escale_core.store import InMemoryReservationStore, ReservationStore
from escale_core.transit_edit import new_boat, new_bus
from escale_core.trips import Trip, TripFilter, active_trip, browse, group
from escale_flet.detail_view import detail_view
from escale_flet.editor import EditorKind, action_editor
from escale_flet.flight_editor import flight_kind
from escale_flet.import_sheet import confirmation_sheet, headline, phone_sheet
from escale_flet.manual_entry import kind_chooser
from escale_flet.preferences import Preferences
from escale_flet.stay_editor import STAY
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
from escale_flet.transit_editor import KINDS as TRANSIT
from escale_flet.trips_view import search_field, trips_bar, trips_page, trips_sections

NARROW_BELOW = 550
"""Window width (logical px) under which the tabs move to a bottom bar (ADR-0007)."""


COMPACT_BELOW = 400
SHEET_BELOW = 450
"""Under this width the editor is a bottom sheet, as libadwaita's AdwDialog in auto mode."""
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

Writer = Callable[[ExtractedReservation, Any], ExtractedReservation]
"""Writes an editor's fields into a booking (S017b, S029a)."""

IMPORT_ENTRY = "Import a file…"
MANUAL_ENTRY = "Add manually…"
ADD_MENU_ENTRIES: tuple[str, ...] = (
    "Search a train…",
    IMPORT_ENTRY,
    "Scan or paste…",
    "New trip…",
    "New outing…",
    MANUAL_ENTRY,
)
"""The mockup's "Add" menu; entries other than import wait for their stories."""

"""libadwaita's standard control radius, used by the "Add" split button."""

IMPORT_EXTENSIONS = ["pdf", "pkpass", "ics", "itinerary", "html", "eml", "png", "jpg", "jpeg"]
"""What kitinerary-extractor reads (ADR-0003)."""

PHONES = {ft.PagePlatform.ANDROID, ft.PagePlatform.IOS, ft.PagePlatform.ANDROID_TV}

FileChooser = Callable[[], Awaitable[Path | None]]
Sharer = Callable[[str], Awaitable[str | None]]
"""Shares a text; returns a message to confirm it (``None``: the system showed its own)."""


def toast(text: str, window: float | None = None, duration: int = 4000) -> ft.SnackBar:
    """A short notice floating at the bottom, as libadwaita's AdwToast (ADR-0008)."""
    return ft.SnackBar(
        ft.Text(text),
        behavior=ft.SnackBarBehavior.FLOATING,
        shape=ft.RoundedRectangleBorder(radius=22),
        width=min(460, (window or 460) - 24),
        duration=duration,
    )


def changed_elsewhere(titles: Sequence[str]) -> str:
    """The toast after a run where the server's version won over a local change (S008c)."""
    if len(titles) == 1:
        return f"{titles[0]} was changed on another device; that version is kept."
    return f"{len(titles)} reservations were changed on another device; those versions are kept."


NOT_ON_DEVICE = (
    "This document is not on this device yet. It downloads when the server can be reached."
)
"""The toast when a document cannot be downloaded now (S009b)."""


def shares_with_sheet(platform: ft.PagePlatform | None) -> bool:
    """Phones have a share sheet; elsewhere Escale copies the text instead (S016)."""
    return platform in (ft.PagePlatform.ANDROID, ft.PagePlatform.IOS)


def _editor_height(window: object, sheet: bool) -> float:
    """Most of the window for a bottom sheet; at most 640 px for a floating dialog."""
    if not isinstance(window, int | float) or not window:
        return 640
    return window * 0.9 if sheet else min(640, window * 0.8)


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


def _add_menu_items(
    on_import: Callable[[Any], Awaitable[None]], on_manual: Callable[[Any], None]
) -> list[ft.PopupMenuItem]:
    actions: dict[str, Callable[[Any], Any]] = {IMPORT_ENTRY: on_import, MANUAL_ENTRY: on_manual}
    return [
        ft.PopupMenuItem(content=ft.Text(entry), on_click=actions[entry])
        if entry in actions
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
        launch: Callable[[str], Awaitable[None]] | None = None,
        account: Account | None = None,
        sync: Callable[[], Awaitable[object]] | None = None,
        documents: Documents | None = None,
    ) -> None:
        if importer is None:
            importer = Importer(KitineraryCli(), store or InMemoryReservationStore())
        self.importer = importer
        self.account = account
        self.sync = sync
        """Sends local changes to the calendar (S008a); run after each of them."""
        self.documents = documents
        """Downloads the documents this device lacks (S009b)."""
        self.preferences: Preferences | None = None
        self.store: ReservationStore = store or importer.store
        self.clock: Callable[[], datetime] = clock or (lambda: datetime.now().astimezone())
        self.trip: Trip | None = None
        """The active trip, shown in "Current"."""
        self.trips: list[Trip] = []
        self.browsed: Trip | None = None
        """The trip opened from "My trips", as a pushed page (S035, ADR-0007)."""
        self.trip_kind: TripFilter = "all"
        self.trip_query = ""
        self._trip_search = search_field(self._on_trip_query)
        self._trip_sections = ft.Container(expand=True)
        self.ticket: ExtractedReservation | None = None
        self.detail: ExtractedReservation | None = None
        self.editing = False
        self._editor: ft.AlertDialog | ft.BottomSheet | None = None
        self._picker: ft.DialogControl | None = None
        self.adding: ExtractedReservation | None = None
        """A booking added by hand (S018), while its editor is open."""
        self._chooser: ft.DialogControl | None = None
        """The kinds of booking to add by hand, while shown."""
        """A date or time picker opened from the editor, above it."""
        self.highlight: str | None = None
        self.scroll_target: str | None = None
        self.width: float | None = None
        self._timeline: ft.Column | None = None
        self.choose_file: FileChooser = choose_file or self._pick_file
        self.share: Sharer = share or self._share_text
        self.launch: Callable[[str], Awaitable[None]] = launch or self._launch_url
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
        # libadwaita's AdwSplitButton in a header bar: flat, no suggested style (ADR-0008);
        # the main action (import) and its menu, a thin separator between.
        self.add_button = ft.Row(
            [
                ft.TextButton(
                    "Add",
                    icon=ft.Icons.ADD,
                    tooltip="Import a file",
                    on_click=self._on_import,
                    style=ft.ButtonStyle(color=ft.Colors.ON_SURFACE),
                ),
                ft.Container(
                    width=1, height=20, bgcolor=ft.Colors.with_opacity(0.2, ft.Colors.ON_SURFACE)
                ),
                ft.PopupMenuButton(
                    icon=ft.Icons.ARROW_DROP_DOWN,
                    tooltip="Add…",
                    items=_add_menu_items(self._on_import, self._on_add_manually),
                ),
            ],
            spacing=0,
            tight=True,
        )
        self.add_menu_compact = ft.PopupMenuButton(
            icon=ft.Icons.ADD,
            tooltip="Add…",
            items=_add_menu_items(self._on_import, self._on_add_manually),
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
        was_compact, was_sheet, was_columns = self._compact(), self._sheet(), self._columns()
        self.width = width
        layout = layout_for(width)
        changed = layout != self.layout or self._compact() != was_compact
        listing = self.selected == Tab.TRIPS and self.browsed is None
        changed = changed or (listing and self._columns() != was_columns)
        if changed:
            self.layout = layout
            self._apply()
        if self.preferences is not None and self._sheet() != was_sheet:
            if self._page is not None:
                self._page.pop_dialog()  # the same preferences, rebuilt for the new width
            self._show_preferences()
        elif self.editing and self._editor is not None and self._sheet() != was_sheet:
            self._fit_editor()
        elif self._chooser is not None and self._sheet() != was_sheet:
            self._close_chooser(None)  # the same kinds, as the other presentation
            self.add_manually()
        elif changed:
            self._update()

    def _sheet(self) -> bool:
        """Under 450 px the editor is a bottom sheet (libadwaita's AdwDialog, ADR-0008)."""
        return self.width is not None and self.width < SHEET_BELOW

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

    @staticmethod
    def _editor_for(r: ExtractedReservation) -> tuple[EditorKind[Any], Writer] | None:
        """The editor of a booking and what writes its fields back, if it has one."""
        if r.type == "LodgingReservation":  # S017b
            return STAY, stays.edited
        if r.type == "FlightReservation":  # S029a
            return flight_kind(r), flight_edit.edited
        if r.type in TRANSIT:  # S030
            return TRANSIT[r.type], transit_edit.edited
        return None

    def edit(self, values: Any = None) -> None:
        """The detail's editor, as an action dialog (S061); ``values``: what was typed
        before the window crossed 450 px."""
        target = self.adding or self.detail
        found = self._editor_for(target) if target is not None else None
        if found is None or target is None or self._page is None:
            return
        kind = found[0]
        if self.adding is not None:
            kind = replace(kind, title=kind.title.replace("Edit", "New", 1))
        self.editing = True
        height = getattr(self._page, "height", None)
        self._editor = action_editor(
            kind,
            target,
            self.save_edit,
            self._on_cancel_edit,
            self._on_editor_dismissed,
            sheet=self._sheet(),
            height=_editor_height(height, self._sheet()),
            initial=values,
            show=self._show_picker,
        )
        self._page.show_dialog(self._editor)
        self._update()

    def _show_picker(self, picker: ft.DialogControl) -> None:
        if self._page is not None:
            self._picker = picker
            fill: Any = getattr(picker, "on_change", None)

            def picked(e: Any) -> None:  # OK: Flutter sends no dismissal then
                if fill is not None:
                    fill(e)
                self._on_picker_closed(e)

            picker.on_change = picked  # type: ignore[attr-defined]
            picker.on_dismiss = self._on_picker_closed
            self._page.show_dialog(picker)

    def _on_picker_closed(self, _: Any) -> None:
        self._picker = None
        self._fit_editor()

    def _fit_editor(self) -> None:
        """Rebuild the editor as a dialog or a bottom sheet if the width asks for the
        other one; not while a picker is open above it, as Flutter would leave the
        picker on screen."""
        editor = self._editor
        if not self.editing or editor is None or self._picker is not None:
            return
        if isinstance(editor, ft.BottomSheet) != self._sheet():
            values = editor.data["values"]()  # keep what was typed
            self._close_editor()
            self.edit(values)

    def _close_editor(self) -> None:
        if self.editing and self._page is not None:
            self.editing = False
            self._page.pop_dialog()

    def cancel_edit(self) -> None:
        self._close_editor()
        self.adding = None
        self._update()

    def _on_editor_dismissed(self, e: Any) -> None:
        # Esc or a click outside: the dialog is already gone. Not an editor replaced by
        # one of the other presentation, whose dismissal arrives after the new one opened.
        if getattr(e, "control", self._editor) is self._editor:
            self.editing = False
            self.adding = None

    # --- adding by hand (S018) ---

    def add_manually(self) -> None:
        """The kinds of booking to add by hand."""
        if self._page is not None:
            chooser = kind_chooser(self._on_manual_kind, self._close_chooser, sheet=self._sheet())
            chooser.on_dismiss = self._on_chooser_dismissed
            self._chooser = chooser
            self._page.show_dialog(chooser)

    def _close_chooser(self, _: Any) -> None:
        if self._chooser is not None and self._page is not None:
            self._chooser = None
            self._page.pop_dialog()

    def _on_chooser_dismissed(self, e: Any) -> None:
        if getattr(e, "control", self._chooser) is self._chooser:
            self._chooser = None

    def _on_add_manually(self, _: Any) -> None:
        self.add_manually()

    def _on_manual_kind(self, key: str) -> None:
        self._close_chooser(None)
        blank = {"stay": new_stay, "bus": new_bus, "ferry": new_boat}.get(key)
        if blank is not None:
            self.new_booking(blank())

    def new_booking(self, blank: ExtractedReservation) -> None:
        """The editor of ``blank``, empty; saving adds it to the store."""
        self.adding = blank
        self.edit()

    async def _save_new(self, new: ExtractedReservation) -> None:
        self.adding = None
        await self.store.add(None, [new])
        self._regroup(group(await self.store.reservations()))
        trip = next((t for t in self.trips if new in t.reservations), None)
        if trip is not None:
            if trip is self.trip:
                self.selected, self.browsed = Tab.CURRENT, None
            else:
                self.selected, self.browsed = Tab.TRIPS, trip
            self.detail = next(r for r in trip.reservations if r == new)
            self.highlight = segment_ref(self.detail)
        self._apply()
        self._update()
        await self._synced()

    edit_stay = edit

    async def save_edit(self, values: Any) -> None:
        """Write the edited booking to the store, then show its detail again."""
        old = self.adding or self.detail
        found = self._editor_for(old) if old is not None else None
        if old is None or found is None:
            return
        new = found[1](old, values)
        self._close_editor()
        if self.adding is not None:
            await self._save_new(new)
            return
        await self.store.replace(old, new)
        self._regroup(group(await self.store.reservations()))
        shown = self._shown()
        kept = [r for r in shown.reservations if r == new] if shown else []
        self.detail = kept[0] if kept else None
        if self.detail is not None:
            self.highlight = segment_ref(self.detail)
        self._apply()
        self._update()
        await self._synced()

    save_stay = save_edit

    async def _synced(self) -> None:
        await self.synchronise()

    async def synchronise(self) -> None:
        """Run the sync; show what it received (S008b). A detail whose reservation
        changed or went away elsewhere is closed."""
        if self.sync is None:
            return
        report = await self.sync()
        if getattr(report, "received", 0):
            titles = [segment_ref_title(r) for r in getattr(report, "changed_elsewhere", ())]
            self._regroup(group(await self.store.reservations()))
            shown = self._shown()
            if self.detail is not None and (shown is None or self.detail not in shown.reservations):
                self.detail = None
            self._apply()
            if titles and self._page is not None:
                self._page.show_dialog(toast(changed_elsewhere(titles), self.width))
            self._update()
        # the current trip's documents, so that they open offline (S009b)
        if (
            self.documents is not None
            and self.trip is not None
            and await self.documents.prefetch(self.trip.reservations)
        ):
            self._apply()
            self._update()
        if self.documents is not None:
            # then past trips' copies go, over the size limit (S009c)
            await self.documents.clean(group(await self.store.reservations()), self.clock())

    # --- preferences (S006b) ---

    async def open_preferences(self) -> None:
        if self.account is None or self._page is None:
            return
        self.preferences = Preferences(self.account, self._on_close_preferences, self._synced)
        self._show_preferences()
        if self.account.connected and not self.account.calendars:
            await self.preferences.load()

    def _show_preferences(self) -> None:
        if self.preferences is None or self._page is None:
            return
        height = getattr(self._page, "height", None)
        self._page.show_dialog(
            self.preferences.dialog(
                self._on_preferences_dismissed,
                sheet=self._sheet(),
                height=min(_editor_height(height, self._sheet()), 480),
            )
        )
        self._update()

    def _close_preferences(self) -> None:
        if self.preferences is not None and self._page is not None:
            self.preferences = None
            self._page.pop_dialog()

    def _on_close_preferences(self, _: Any) -> None:
        self._close_preferences()
        self._update()

    def _on_preferences_dismissed(self, _: Any) -> None:
        self.preferences = None  # Esc, a click outside or a swipe: already gone

    async def _on_preferences(self, _: Any) -> None:
        await self.open_preferences()

    def _primary_menu(self) -> list[ft.Control]:
        """The main menu, last in the header bar of the main views (ADR-0008)."""
        if self.account is None:
            return []
        return [
            ft.PopupMenuButton(
                icon=ft.Icons.MENU,
                tooltip="Main Menu",
                items=[
                    ft.PopupMenuItem(content=ft.Text("Preferences"), on_click=self._on_preferences)
                ],
                data={"primary_menu": True},
            )
        ]

    def _on_edit(self, _: Any) -> None:
        self.edit()

    def _on_cancel_edit(self, _: Any) -> None:
        self.cancel_edit()

    async def close_detail(self) -> None:
        ref = segment_ref(self.detail) if self.detail is not None else None
        self.detail = None
        self.editing = False
        if ref is None:
            self._apply()
            self._update()
            return
        await self.jump(ref)

    async def _on_jump(self, reservation: ExtractedReservation) -> None:
        await self.jump(segment_ref(reservation))

    def _open_jump_sheet(self, _: Any) -> None:
        trip = self._shown()
        if self._page is None or trip is None:
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
                            *jump_entries(trip, jump_from_sheet),
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
        trip = self._shown()
        if trip is None or self.layout == Layout.WIDE:
            return None
        if self._compact():
            return ft.IconButton(
                ft.Icons.FORMAT_LIST_BULLETED,
                tooltip="Jump to…",
                on_click=self._open_jump_sheet,
                data={"jump_sheet": True},
            )
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
        self._regroup(group(await self.store.reservations()))
        self._apply()
        self._update()

    def _regroup(self, trips: list[Trip]) -> None:
        """The trips after a change; an opened trip stays open if it is still there."""
        self.trips = trips
        self.trip = active_trip(trips, self.clock())
        if self.browsed is not None:
            start = self.browsed.start
            self.browsed = next((t for t in trips if t.start == start), None)

    def _shown(self) -> Trip | None:
        """The trip whose timeline the selected tab shows."""
        if self.selected == Tab.CURRENT:
            return self.trip
        return self.browsed if self.selected == Tab.TRIPS else None

    # --- "My trips" (S035) ---

    def open_trip(self, trip: Trip) -> None:
        self.browsed, self.detail, self.highlight = trip, None, None
        self._apply()
        self._update()

    def close_trip(self) -> None:
        self.browsed, self.detail = None, None
        self._apply()
        self._update()

    def _on_close_trip(self, _: Any) -> None:
        self.close_trip()

    def _on_trip_kind(self, kind: TripFilter) -> None:
        self.trip_kind = kind
        self._apply()
        self._update()

    def _on_trip_query(self, query: str) -> None:
        self.trip_query = query
        self._trip_sections.content = self._sections()  # the search entry keeps its focus
        self._update()

    def _columns(self) -> int:
        width = self.width or 1000
        return 1 if width < NARROW_BELOW else 2 if width < 900 else 3

    def _sections(self) -> ft.Control:
        found = browse(self.trips, self.clock(), self.trip_kind, self.trip_query)
        return trips_sections(found, self.open_trip, self._columns())

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
        """Open the reservation's document: the copy on this device, else downloaded
        (S009b); ``None`` when there is no way to get one."""
        locate = getattr(self.store, "document_path", None)
        if locate is None or self._page is None or not reservation.subject_of:
            return None
        local = next((p for d in reservation.subject_of if (p := locate(d))), None)
        connected = self.account is not None and self.account.connected
        if local is None and (self.documents is None or not connected):
            return None

        async def open_it(_: Any) -> None:
            path = local
            if path is None and self.documents is not None:
                for document_id in reservation.subject_of:
                    path = await self.documents.local(document_id)
                    if path is not None:
                        break
            if path is None:
                if self._page is not None:
                    self._page.show_dialog(toast(NOT_ON_DEVICE, self.width))
                return
            await self.launch(path.as_uri())

        return open_it

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
                self._page.show_dialog(toast(message, self.width))

        return share_it

    async def _launch_url(self, url: str) -> None:
        """A link handed to the system: browser, dialler, mail app (S017a)."""
        if isinstance(self._page, ft.Page):
            await ft.UrlLauncher().launch_url(url)

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
        await self.open_file(path)

    async def open_file(self, path: Path) -> None:
        """The import confirmation for ``path``: a chosen file, or one opened with
        Escale (S025a)."""
        page = self._page
        if page is None:
            return
        result = await self.importer.preview(path)

        async def confirm(_: Any) -> None:
            await self.importer.confirm(result)
            await self.refresh()
            self._close_sheet(None)
            await self._synced()

        def manual(_: Any) -> None:
            self._close_sheet(None)
            self.add_manually()

        page.show_dialog(confirmation_sheet(result, confirm, self._close_sheet, manual))

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
        self.appbar.leading_width = None
        hide_tabs = False
        shown = self._shown()
        pushed = self.selected == Tab.TRIPS and shown is not None
        if shown is not None and self.detail is not None:
            self.body.content = ft.Container(
                detail_view(
                    self.detail,
                    self._ticket_handler(self.detail) if has_ticket(self.detail) else None,
                    self._open_document(self.detail),
                    self._share_flight(self.detail),
                    self.launch,
                    titled=self.layout == Layout.WIDE,
                ),
                max_width=MAX_WIDTH,
                expand=True,
            )
            self.body.alignment = ft.Alignment.TOP_CENTER
            hide_tabs = self._compact() or pushed
        elif shown is not None:
            hide_tabs = pushed
            self._timeline = trip_view(
                shown,
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
                        jump_panel(shown, self._on_jump),
                        ft.Container(self._timeline, expand=True),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    expand=True,
                )
            self.body.content = ft.Container(content, max_width=MAX_WIDTH + 260, expand=True)
            self.body.alignment = ft.Alignment.TOP_CENTER
        elif self.selected == Tab.TRIPS and self.trips:
            self._trip_sections.content = self._sections()
            bar = trips_bar(
                self.trip_kind, self._on_trip_kind, self._trip_search, self._columns() == 1
            )
            self.body.content = trips_page(bar, self._trip_sections)
            self.body.alignment = ft.Alignment.TOP_CENTER
        else:
            self.body.content = _empty_view(_spec(self.selected))
            self.body.alignment = ft.Alignment.CENTER
        wide = self.layout == Layout.WIDE
        in_detail = shown is not None and self.detail is not None
        if wide:
            self.appbar.title = self.switcher
            add: ft.Control = self.add_button
            navigation_bar = None
        else:
            self.appbar.title = ft.Text(_spec(self.selected).label)
            add = self.add_menu_compact
            navigation_bar = None if hide_tabs else self.bottom_bar
        # Main actions at the start of the header bar, the rest at the end (ADR-0008).
        self.appbar.leading = add
        self.appbar.leading_width = 150 if wide else None
        self.appbar.actions = [*self._ticket_action(wide=wide), *self._primary_menu()]
        if pushed and shown is not None and not in_detail:
            self._trip_header_bar(shown, wide)
            navigation_bar = None
        if in_detail and shown is not None and self.detail is not None:
            self._detail_header_bar(shown.name, self.detail, wide)
            if pushed:
                navigation_bar = None
        if self._page is not None:
            self._page.navigation_bar = navigation_bar

    def _trip_header_bar(self, trip: Trip, wide: bool) -> None:
        """A trip opened from "My trips": back to the list in place of the tabs (ADR-0007)."""
        tooltip = "Back to My trips"
        icon = ft.Icons.ARROW_BACK_IOS_NEW
        self.appbar.leading = (
            ft.TextButton(
                "My trips",
                icon=icon,
                tooltip=tooltip,
                on_click=self._on_close_trip,
                data={"back": "trips"},
            )
            if wide
            else ft.IconButton(
                icon, tooltip=tooltip, on_click=self._on_close_trip, data={"back": "trips"}
            )
        )
        self.appbar.leading_width = 180 if wide else None
        self.appbar.title = ft.Text(trip.name, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
        self.appbar.actions = [*self._ticket_action(wide=wide), *self._primary_menu()]

    def _detail_header_bar(self, trip: str, detail: ExtractedReservation, wide: bool) -> None:
        """Back at the start, Edit at the end; Add is hidden (S061, ADR-0008)."""
        tooltip = f"Back to {trip}"
        icon = ft.Icons.ARROW_BACK_IOS_NEW
        self.appbar.leading = (
            ft.TextButton(
                trip,
                icon=icon,
                tooltip=tooltip,
                on_click=self._on_close_detail,
                data={"back": True},
            )
            if wide
            else ft.IconButton(
                icon, tooltip=tooltip, on_click=self._on_close_detail, data={"back": True}
            )
        )
        self.appbar.leading_width = 180 if wide else None
        if not wide:
            self.appbar.title = ft.Text(
                segment_ref_title(detail), max_lines=1, overflow=ft.TextOverflow.ELLIPSIS
            )
        edit = (
            [
                ft.IconButton(
                    ft.Icons.EDIT_OUTLINED,
                    tooltip="Edit",
                    on_click=self._on_edit,
                    data={"edit": True},
                )
            ]
            if self._editor_for(detail) is not None
            else []
        )
        self.appbar.actions = [*edit, *self._ticket_action(wide=wide)]

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
                ft.TextButton(
                    "Ticket",
                    icon=icon,
                    tooltip=tooltip,
                    on_click=self._on_current_ticket,
                    style=ft.ButtonStyle(color=ft.Colors.ON_SURFACE),
                ),
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
