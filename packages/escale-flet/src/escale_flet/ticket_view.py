"""A ticket full screen, with its barcode, readable offline (S015, mockup step 3)."""

from __future__ import annotations

import base64
from collections.abc import Callable
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation
from escale_core.tickets import ticket_of
from escale_flet.barcode import png
from escale_flet.import_sheet import format_when, headline, route, travellers

Action = Callable[[Any], Any]
MAX_WIDTH = 520


def _seat(r: ExtractedReservation) -> str | None:
    ticket = r.raw.get("reservedTicket")
    seat = ticket.get("ticketedSeat") if isinstance(ticket, dict) else None
    if not isinstance(seat, dict):
        return None
    coach, number = seat.get("seatSection"), seat.get("seatNumber")
    parts = [
        f"Coach {coach}" if isinstance(coach, str) else None,
        f"Seat {number}" if isinstance(number, str) else None,
    ]
    return " · ".join(p for p in parts if p) or None


def ticket_view(r: ExtractedReservation, open_document: Action | None) -> ft.Control:
    """The ticket: what it is for, the barcode on white, its number; else the document."""
    ticket = ticket_of(r)
    when = r.departure.time if r.departure and r.departure.time else None
    facts = [format_when(when) if when else None, _seat(r)]
    lines: list[ft.Control] = [ft.Text(headline(r), theme_style=ft.TextThemeStyle.HEADLINE_SMALL)]
    where = route(r)
    if where:
        lines.append(ft.Text(where, theme_style=ft.TextThemeStyle.TITLE_MEDIUM))
    lines.append(ft.Text(" · ".join(f for f in facts if f), opacity=0.7))
    names = travellers(r)
    if names:
        lines.append(ft.Text(", ".join(names), opacity=0.7))
    image = png(ticket.barcode) if ticket.barcode else None
    if image is not None:
        lines.append(
            ft.Container(
                ft.Image(
                    src=base64.b64encode(image).decode(),
                    fit=ft.BoxFit.CONTAIN,
                    filter_quality=ft.FilterQuality.NONE,
                    semantics_label="Ticket barcode",
                ),
                bgcolor=ft.Colors.WHITE,
                padding=16,
                border_radius=12,
                data={"barcode": ticket.barcode},
            )
        )
        if ticket.number:
            lines.append(
                ft.Text(ticket.number, theme_style=ft.TextThemeStyle.TITLE_MEDIUM, selectable=True)
            )
        lines.append(ft.Text("Shown from the copy on this device: no network needed.", opacity=0.7))
    else:
        reason = (
            "Escale cannot draw this ticket's code yet."
            if ticket.barcode
            else "This booking has no barcode."
        )
        lines += [
            ft.Text(reason),
            ft.FilledButton(
                "Open the original document",
                icon=ft.Icons.DESCRIPTION_OUTLINED,
                on_click=open_document,
                disabled=open_document is None,
            ),
        ]
    return ft.Column(
        lines,
        spacing=12,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )
