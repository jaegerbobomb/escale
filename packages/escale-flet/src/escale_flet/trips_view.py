"""The "My trips" list (S035): trips and outings as cards, a filter and a search.

As in the mockup's "Mes voyages" page: an AdwToggleGroup-like filter (All / Trips /
Outings) and a search entry above the list; "Upcoming", then past trips by year; each
card shows its kind, name, dates and what it holds. Outings are purple (Adwaita
``#9141ac``). A click opens the trip's timeline as a pushed page (ADR-0007).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

import flet as ft

from escale_core.trips import Trip, TripFilter
from escale_flet.theme import OUTING
from escale_flet.timeline import _ICONS, CARD_RADIUS, MAX_WIDTH, date_range

FILTERS: tuple[tuple[TripFilter, str], ...] = (
    ("all", "All"),
    ("trip", "Trips"),
    ("outing", "Outings"),
)
_ORDER = (
    "FlightReservation",
    "TrainReservation",
    "BusReservation",
    "BoatReservation",
    "LodgingReservation",
    "EventReservation",
    "FoodEstablishmentReservation",
)


def kinds(trip: Trip) -> list[str]:
    """The reservation types of a trip, the main one first (flight, train, …)."""
    found = {r.type for r in trip.reservations}
    return [t for t in _ORDER if t in found] + sorted(found - set(_ORDER))


def _when(trip: Trip) -> str:
    if trip.kind == "outing":
        start = trip.start
        return f"{date_range(start, start)} · from {start.hour:02d}:{start.minute:02d}"
    return date_range(trip.start, trip.end)


def _count(trip: Trip) -> str:
    n = len(trip.reservations)
    word = "place" if trip.kind == "outing" else "segment"
    return f"{n} {word}{'s' if n > 1 else ''}"


def _pill(content: ft.Control, bgcolor: str) -> ft.Control:
    return ft.Container(
        content,
        bgcolor=bgcolor,
        padding=ft.Padding.symmetric(horizontal=9, vertical=3),
        border_radius=11,
    )


def trip_card(trip: Trip, on_open: Callable[[Trip], Any]) -> ft.Control:
    outing = trip.kind == "outing"
    tone = OUTING if outing else ft.Colors.SECONDARY
    soft = ft.Colors.with_opacity(0.13, tone)
    neutral = ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE)
    types = kinds(trip)
    icon = _ICONS.get(types[0], ft.Icons.EVENT_NOTE_OUTLINED) if types else ft.Icons.LUGGAGE
    badge = ft.Text(
        "Outing" if outing else "Trip", size=11.5, weight=ft.FontWeight.W_700, color=tone
    )
    small: list[ft.Control] = [
        ft.Icon(
            _ICONS.get(t, ft.Icons.EVENT_NOTE_OUTLINED), size=14, color=ft.Colors.ON_SURFACE_VARIANT
        )
        for t in types
    ]
    return ft.Container(
        ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            ft.Icon(icon, size=18, color=tone),
                            width=36,
                            height=36,
                            border_radius=10,
                            bgcolor=soft,
                            alignment=ft.Alignment.CENTER,
                        ),
                        _pill(badge, soft),
                    ],
                    spacing=9,
                ),
                ft.Column(
                    [
                        ft.Text(
                            trip.name,
                            size=16,
                            weight=ft.FontWeight.W_700,
                            max_lines=1,
                            overflow=ft.TextOverflow.ELLIPSIS,
                        ),
                        ft.Text(_when(trip), size=12.5, color=ft.Colors.ON_SURFACE_VARIANT),
                    ],
                    spacing=3,
                ),
                ft.Row(
                    [
                        _pill(
                            ft.Text(
                                _count(trip),
                                size=11.5,
                                color=tone if outing else ft.Colors.ON_SURFACE,
                                weight=ft.FontWeight.W_700 if outing else None,
                            ),
                            soft if outing else neutral,
                        ),
                        _pill(ft.Row(small, spacing=6, tight=True), neutral),
                    ],
                    spacing=6,
                    wrap=True,
                ),
            ],
            spacing=12,
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border.all(1, OUTING if outing else ft.Colors.OUTLINE),
        border_radius=CARD_RADIUS,
        padding=ft.Padding.symmetric(horizontal=16, vertical=15),
        on_click=lambda _: on_open(trip),
        ink=True,
        expand=True,
        data={"trip_card": trip.name},
    )


def _grid(trips: Sequence[Trip], columns: int, on_open: Callable[[Trip], Any]) -> ft.Control:
    rows: list[ft.Control] = []
    for i in range(0, len(trips), columns):
        cards = [trip_card(t, on_open) for t in trips[i : i + columns]]
        cards += [ft.Container(expand=True) for _ in range(columns - len(cards))]
        rows.append(ft.Row(cards, spacing=14, vertical_alignment=ft.CrossAxisAlignment.START))
    return ft.Column(rows, spacing=14)


def search_field(on_query: Callable[[str], Any]) -> ft.TextField:
    """The search entry; made once, so that typing keeps its focus."""
    return ft.TextField(
        hint_text="Search…",
        prefix_icon=ft.Icons.SEARCH,
        dense=True,
        border_radius=8,
        filled=True,
        fill_color=ft.Colors.with_opacity(0.06, ft.Colors.ON_SURFACE),
        border=ft.InputBorder.NONE,
        on_change=lambda e: on_query(e.control.value or ""),
        data={"trip_search": True},
    )


def trips_bar(
    kind: TripFilter, on_kind: Callable[[TripFilter], Any], search: ft.TextField, narrow: bool
) -> ft.Control:
    """The filter (All / Trips / Outings) and the search entry."""
    toggle = ft.SegmentedButton(
        segments=[ft.Segment(value=value, label=ft.Text(label)) for value, label in FILTERS],
        selected=[kind],
        allow_empty_selection=False,
        show_selected_icon=False,
        on_change=lambda e: on_kind(e.control.selected[0]),
        data={"trip_filter": True},
    )
    search.width = None if narrow else 230
    search.expand = narrow
    if narrow:
        return ft.Column(
            [toggle, ft.Row([search])],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        )
    return ft.Row([toggle, ft.Container(expand=True), search])


def trips_sections(
    sections: Sequence[tuple[str, Sequence[Trip]]], on_open: Callable[[Trip], Any], columns: int
) -> ft.Control:
    """ "Upcoming", then past trips by year, as grids of cards."""
    body: list[ft.Control] = []
    for title, trips in sections:
        body.append(
            ft.Text(
                f"{title.upper()} · {len(trips)}",
                size=11.5,
                weight=ft.FontWeight.W_700,
                color=ft.Colors.ON_SURFACE_VARIANT,
                data={"section": title},
            )
        )
        body.append(_grid(trips, columns, on_open))
    if not sections:
        body.append(
            ft.Container(
                ft.Text("No trip matches.", color=ft.Colors.ON_SURFACE_VARIANT),
                padding=ft.Padding.only(top=24),
                alignment=ft.Alignment.CENTER,
            )
        )
    return ft.Column(body, spacing=12, scroll=ft.ScrollMode.AUTO, expand=True)


def trips_page(bar: ft.Control, sections: ft.Container) -> ft.Control:
    return ft.Container(
        ft.Column([bar, sections], spacing=18, expand=True),
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        max_width=MAX_WIDTH + 340,
        expand=True,
    )
