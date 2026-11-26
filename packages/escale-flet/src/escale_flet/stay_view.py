"""A stay's detail, laid out as the mockup's "Nuit d'hôtel" (S017a).

Identity (icon, name, address), a strip with check-in, check-out and the number of
nights, the booking's facts as label/value rows, the contact, then the main action (a pill) and
the others as rows (ADR-0008). The
mockup's photo, price and map need data Escale does not have yet.
"""

from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation
from escale_core.stays import address, cancelled, contact, manage_link
from escale_core.trips import span
from escale_flet.import_sheet import travellers

Action = Callable[[Any], Any]
Opener = Callable[[str], Awaitable[None]]
"""Hands a link (``https:``, ``tel:``, ``mailto:``) to the system."""

_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)  # fmt: skip
_TINT = ft.Colors.with_opacity(0.14, ft.Colors.PRIMARY)
_RADIUS = 14


def opens(open_url: Opener, link: str) -> Callable[[Any], Awaitable[None]]:
    async def go(_: Any) -> None:
        await open_url(link)

    return go


def primary(label: str, on_click: Action) -> ft.Control:
    """The view's one suggested action: label only, pill-shaped (ADR-0008)."""
    return ft.FilledButton(
        label,
        on_click=on_click,
        style=ft.ButtonStyle(
            shape=ft.StadiumBorder(), padding=ft.Padding.symmetric(horizontal=24, vertical=14)
        ),
    )


def action_rows(rows: list[tuple[ft.IconData, str, Action]]) -> ft.Control:
    """Secondary actions as a boxed list: a label, a symbolic icon at the end."""
    return _facts(
        [
            ft.Container(
                ft.Row(
                    [
                        ft.Text(label, size=14, expand=True),
                        ft.Icon(icon, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                    ]
                ),
                padding=ft.Padding.symmetric(horizontal=16, vertical=14),
                on_click=on_click,
                data={"action": label},
            )
            for icon, label, on_click in rows
        ]
    )


def _card(content: ft.Control) -> ft.Control:
    return ft.Container(
        content,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=_RADIUS,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


def _identity(r: ExtractedReservation, titled: bool = True) -> ft.Control:
    place = r.raw.get("reservationFor")
    name = place.get("name") if isinstance(place, dict) else None
    where = address(r)
    return ft.Row(
        [
            ft.Container(
                ft.Icon(ft.Icons.HOTEL_OUTLINED, size=22, color=ft.Colors.PRIMARY),
                width=42,
                height=42,
                border_radius=11,
                bgcolor=_TINT,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column(
                [
                    *(
                        [
                            ft.Text(
                                name if isinstance(name, str) else "Stay",
                                size=22,
                                weight=ft.FontWeight.W_700,
                            )
                        ]
                        if titled
                        else []
                    ),
                    *(
                        [ft.Text(where, size=13, color=ft.Colors.ON_SURFACE_VARIANT)]
                        if where
                        else []
                    ),
                ],
                spacing=2,
                tight=True,
                expand=True,
            ),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.START if titled else ft.CrossAxisAlignment.CENTER,
    )


def _moment(label: str, moment: datetime) -> ft.Control:
    day = f"{_DAYS[moment.weekday()]} {moment.day} {_MONTHS[moment.month - 1]}"
    return ft.Container(
        ft.Column(
            [
                ft.Text(
                    label.upper(),
                    size=11.5,
                    weight=ft.FontWeight.W_700,
                    color=ft.Colors.ON_SURFACE_VARIANT,
                ),
                ft.Text(f"{moment:%H:%M}", size=22, weight=ft.FontWeight.W_700),
                ft.Text(day, size=12.5, color=ft.Colors.ON_SURFACE_VARIANT),
            ],
            spacing=2,
            tight=True,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        expand=True,
        data={"moment": label},
    )


def _strip(start: datetime, end: datetime) -> ft.Control:
    nights = max((end.date() - start.date()).days, 1)
    separator = ft.Container(width=1, bgcolor=ft.Colors.OUTLINE_VARIANT)
    return _card(
        ft.Row(
            [
                _moment("Check-in", start),
                separator,
                _moment("Check-out", end),
                separator,
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(
                                str(nights),
                                size=26,
                                weight=ft.FontWeight.W_700,
                                color=ft.Colors.PRIMARY,
                            ),
                            ft.Text(
                                "night" if nights == 1 else "nights",
                                size=11.5,
                                weight=ft.FontWeight.W_700,
                                color=ft.Colors.PRIMARY,
                            ),
                        ],
                        spacing=0,
                        tight=True,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    width=84,
                    bgcolor=_TINT,
                    alignment=ft.Alignment.CENTER,
                ),
            ],
            spacing=0,
            intrinsic_height=True,
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
        )
    )


def _fact(icon: ft.IconData, label: str, value: str, on_click: Action | None = None) -> ft.Control:
    return ft.Container(
        ft.Row(
            [
                ft.Icon(icon, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                ft.Text(label, size=13.5),
                ft.Text(
                    value,
                    size=13.5,
                    weight=ft.FontWeight.W_700,
                    color=ft.Colors.PRIMARY if on_click else None,
                    text_align=ft.TextAlign.RIGHT,
                    expand=True,
                ),
            ],
            spacing=12,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        on_click=on_click,
        data={"row": label},
    )


def _facts(rows: list[ft.Control]) -> ft.Control:
    listed: list[ft.Control] = []
    for i, row in enumerate(rows):
        if i:
            listed.append(ft.Divider(height=1, thickness=1, color=ft.Colors.OUTLINE_VARIANT))
        listed.append(row)
    return _card(ft.Column(listed, spacing=0, tight=True))


def stay_body(
    r: ExtractedReservation,
    open_url: Opener | None,
    on_document: Action | None,
    titled: bool = True,
) -> list[ft.Control]:
    """A stay's detail; back and Edit are in the header bar (ADR-0008)."""
    body: list[ft.Control] = [_identity(r, titled)]
    timing = span(r)
    if timing is not None:
        body.append(_strip(*timing))
    booking: list[ft.Control] = []
    if r.reference:
        booking.append(
            _fact(ft.Icons.CONFIRMATION_NUMBER_OUTLINED, "Booking reference", r.reference)
        )
    room = r.raw.get("lodgingUnitDescription")
    if isinstance(room, str) and room.strip():
        booking.append(_fact(ft.Icons.BED_OUTLINED, "Room", room.strip()))
    names = travellers(r)
    if names:
        booking.append(_fact(ft.Icons.PERSON_OUTLINE, "Travellers", ", ".join(names)))
    if cancelled(r):
        booking.append(_fact(ft.Icons.EVENT_BUSY_OUTLINED, "Status", "Cancelled"))
    if booking:
        body.append(_facts(booking))
    c = contact(r)
    links = [
        (
            ft.Icons.CALL_OUTLINED,
            "Telephone",
            c.telephone,
            f"tel:{re.sub(r'[^0-9+]', '', c.telephone or '')}",
        ),
        (ft.Icons.MAIL_OUTLINE, "E-mail", c.email, f"mailto:{c.email}"),
        (ft.Icons.LANGUAGE, "Website", c.website, c.website or ""),
    ]
    reach = [
        _fact(icon, label, value, opens(open_url, link) if open_url else None)
        for icon, label, value, link in links
        if value
    ]
    if reach:
        body.append(_facts(reach))
    manage = manage_link(r)
    if open_url is not None and manage is not None:
        body.append(
            ft.Row([primary(f"Manage booking on {manage.site}", opens(open_url, manage.url))])
        )
    if on_document is not None:
        body.append(action_rows([(ft.Icons.DESCRIPTION_OUTLINED, "Booking document", on_document)]))
    return body
