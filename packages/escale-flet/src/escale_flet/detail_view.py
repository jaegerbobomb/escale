"""A segment's detail, in place of the timeline (S011, ADR-0007).

"‹ <trip>" goes back to the timeline, scrolled to the segment with its card highlighted.
A stay shows its full address, room, contact (actionable) and where to manage the
booking (S017a). Editing comes with S012 (train) and S017b (stay).
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable, Mapping
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation
from escale_core.stays import address, cancelled, contact, manage_link
from escale_core.trips import span
from escale_flet.import_sheet import format_when, headline, travellers

Action = Callable[[Any], Any]
Opener = Callable[[str], Awaitable[None]]
"""Hands a link (``https:``, ``tel:``, ``mailto:``) to the system."""
Row = tuple[str, str, str | None]
"""Label, value, and the link the row opens, if any."""


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _opens(open_url: Opener, link: str) -> Callable[[Any], Awaitable[None]]:
    async def go(_: Any) -> None:
        await open_url(link)

    return go


def _row(label: str, value: str, on_click: Action | None = None) -> ft.Control:
    text = ft.Column(
        [
            ft.Text(label, size=12.5, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text(value, size=15, color=ft.Colors.PRIMARY if on_click else None),
        ],
        spacing=2,
        tight=True,
        expand=True,
    )
    trailing = [ft.Icon(ft.Icons.OPEN_IN_NEW, size=16, color=ft.Colors.PRIMARY)] if on_click else []
    return ft.Container(
        ft.Row([text, *trailing], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(horizontal=16, vertical=10),
        on_click=on_click,
        data={"row": label},
    )


def _stay_rows(r: ExtractedReservation) -> list[Row]:
    rows: list[Row] = []
    where = address(r)
    if where:
        rows.append(("Address", where, None))
    room = r.raw.get("lodgingUnitDescription")
    if isinstance(room, str) and room.strip():
        rows.append(("Room", room.strip(), None))
    c = contact(r)
    if c.telephone:
        rows.append(("Telephone", c.telephone, "tel:" + re.sub(r"[^0-9+]", "", c.telephone)))
    if c.email:
        rows.append(("E-mail", c.email, "mailto:" + c.email))
    if c.website:
        rows.append(("Website", c.website, c.website))
    return rows


def _rows(r: ExtractedReservation) -> list[Row]:
    target = _m(r.raw.get("reservationFor"))
    rows: list[Row] = []
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
            rows.append((label, " · ".join(p for p in parts if p), None))
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
                    None,
                )
            )
    else:
        timing = span(r)
        if timing is not None:
            start, end = timing
            if r.type == "LodgingReservation":
                rows += [
                    ("Check-in", format_when(start), None),
                    ("Check-out", format_when(end), None),
                ]
            else:
                rows.append(("When", format_when(start), None))
        if r.type == "LodgingReservation":
            rows += _stay_rows(r)
        else:
            place = _m(target.get("location")) or target
            postal = _m(place.get("address"))
            where = [place.get("name"), postal.get("streetAddress"), postal.get("addressLocality")]
            text = ", ".join(str(w) for w in dict.fromkeys(where) if isinstance(w, str) and w)
            if text:
                rows.append(("Place", text, None))
    names = travellers(r)
    if names:
        rows.append(("Travellers", ", ".join(names), None))
    if r.reference:
        rows.append(("Booking reference", r.reference, None))
    if cancelled(r):
        rows.append(("Status", "Cancelled", None))
    return rows


def detail_view(
    r: ExtractedReservation,
    trip_name: str,
    on_back: Action,
    on_ticket: Action | None,
    on_document: Action | None = None,
    on_share: Action | None = None,
    open_url: Opener | None = None,
) -> ft.Control:
    title = _m(r.raw.get("reservationFor")).get("name") if r.type == "LodgingReservation" else None
    rows = [
        _row(label, value, _opens(open_url, link) if open_url and link else None)
        for label, value, link in _rows(r)
    ]
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
    manage = manage_link(r) if open_url is not None else None
    if open_url is not None and manage is not None:
        actions.append(
            ft.OutlinedButton(
                f"Manage booking on {manage.site}",
                icon=ft.Icons.OPEN_IN_NEW,
                on_click=_opens(open_url, manage.url),
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
