"""A segment's detail, in place of the timeline (S011, ADR-0007).

"‹ <trip>" goes back to the timeline, scrolled to the segment with its card highlighted.
Editing comes with S012 (train) and S017 (stay).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation
from escale_core.trips import span
from escale_flet.import_sheet import format_when, headline, travellers

Action = Callable[[Any], Any]


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _row(label: str, value: str) -> ft.Control:
    return ft.Container(
        ft.Column(
            [
                ft.Text(label, size=12.5, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(value, size=15),
            ],
            spacing=2,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
    )


def _rows(r: ExtractedReservation) -> list[tuple[str, str]]:
    target = _m(r.raw.get("reservationFor"))
    rows: list[tuple[str, str]] = []
    if r.departure is not None or r.arrival is not None:
        for label, stop, key in (
            ("Departure", r.departure, "departurePlatform"),
            ("Arrival", r.arrival, "arrivalPlatform"),
        ):
            if stop is None:
                continue
            parts = [format_when(stop.time) if stop.time else None, stop.name]
            platform = target.get(key)
            if isinstance(platform, str):
                parts.append(f"Platform {platform}")
            rows.append((label, " · ".join(p for p in parts if p)))
        seat = _m(_m(r.raw.get("reservedTicket")).get("ticketedSeat"))
        coach, number = seat.get("seatSection"), seat.get("seatNumber")
        if isinstance(coach, str) or isinstance(number, str):
            rows.append(
                (
                    "Seat",
                    " · ".join(
                        p
                        for p in (
                            f"Coach {coach}" if isinstance(coach, str) else None,
                            f"Seat {number}" if isinstance(number, str) else None,
                        )
                        if p
                    ),
                )
            )
    else:
        timing = span(r)
        if timing is not None:
            start, end = timing
            if r.type == "LodgingReservation":
                rows += [("Check-in", format_when(start)), ("Check-out", format_when(end))]
            else:
                rows.append(("When", format_when(start)))
        place = _m(target.get("location")) or target
        address = _m(place.get("address"))
        where = [place.get("name"), address.get("streetAddress"), address.get("addressLocality")]
        text = ", ".join(str(w) for w in dict.fromkeys(where) if isinstance(w, str) and w)
        if text:
            rows.append(("Address" if r.type == "LodgingReservation" else "Place", text))
    names = travellers(r)
    if names:
        rows.append(("Travellers", ", ".join(names)))
    if r.reference:
        rows.append(("Booking reference", r.reference))
    return rows


def detail_view(
    r: ExtractedReservation,
    trip_name: str,
    on_back: Action,
    on_ticket: Action | None,
    on_document: Action | None = None,
    on_share: Action | None = None,
) -> ft.Control:
    title = _m(r.raw.get("reservationFor")).get("name") if r.type == "LodgingReservation" else None
    rows = [_row(label, value) for label, value in _rows(r)]
    listed: list[ft.Control] = []
    for i, row in enumerate(rows):
        if i:
            listed.append(ft.Divider(height=1, thickness=1, color=ft.Colors.OUTLINE_VARIANT))
        listed.append(row)
    actions: list[ft.Control] = []
    if on_ticket is not None:
        actions.append(
            ft.FilledTonalButton(
                "Ticket", icon=ft.Icons.CONFIRMATION_NUMBER_OUTLINED, on_click=on_ticket
            )
        )
    elif on_document is not None:
        actions.append(
            ft.FilledTonalButton(
                "Booking document", icon=ft.Icons.DESCRIPTION_OUTLINED, on_click=on_document
            )
        )
    if on_share is not None:
        actions.append(
            ft.OutlinedButton("Share flight", icon=ft.Icons.SHARE_OUTLINED, on_click=on_share)
        )
    return ft.Column(
        [
            ft.TextButton(
                trip_name,
                icon=ft.Icons.ARROW_BACK_IOS_NEW,
                on_click=on_back,
                data={"back": True},
            ),
            ft.Text(
                title if isinstance(title, str) else headline(r),
                size=26,
                weight=ft.FontWeight.W_700,
            ),
            *([ft.Row(actions, wrap=True, spacing=8, run_spacing=8)] if actions else []),
            ft.Container(
                ft.Column(listed, spacing=0, tight=True),
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=12,
            ),
            ft.Text(
                "Editing comes with a later version.", size=12.5, color=ft.Colors.ON_SURFACE_VARIANT
            ),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        data={"detail": r.reference},
    )
