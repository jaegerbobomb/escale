"""A segment's detail, in place of the timeline (S011, ADR-0007).

"‹ <trip>", in the header bar (ADR-0008), goes back to the timeline, scrolled to the
segment with its card highlighted.
A stay (``stay_view``, S017a) and a transport (``transport_view``, S062) have layouts
of their own. Editing comes with S012 (train)
and S017b (stay).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation
from escale_core.stays import cancelled
from escale_core.trips import span
from escale_flet.import_sheet import format_when, headline, travellers
from escale_flet.stay_view import Opener, action_rows, opens, primary, stay_body
from escale_flet.transport_view import transport_body

Action = Callable[[Any], Any]
Row = tuple[str, str, str | None]
"""Label, value, and the link the row opens, if any."""


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


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


def _rows(r: ExtractedReservation) -> list[Row]:
    """Rows of a booking that is neither a transport (``transport_view``) nor a stay."""
    target = _m(r.raw.get("reservationFor"))
    rows: list[Row] = []
    timing = span(r)
    if timing is not None:
        start, _ = timing
        rows.append(("When", format_when(start), None))
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
    on_ticket: Action | None,
    on_document: Action | None = None,
    on_share: Action | None = None,
    open_url: Opener | None = None,
    titled: bool = True,
) -> ft.Control:
    """The booking's detail; back and Edit are in the header bar (ADR-0008). Without
    ``titled`` (a narrow window, whose header bar shows the title) no title repeats it."""
    if r.type == "LodgingReservation":
        return ft.Column(
            stay_body(r, open_url, on_document, titled),
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            data={"detail": r.reference},
        )
    secondary: list[tuple[ft.IconData, str, Action]] = []
    if on_ticket is None and on_document is not None:
        secondary.append((ft.Icons.DESCRIPTION_OUTLINED, "Booking document", on_document))
    if on_share is not None:
        secondary.append((ft.Icons.SHARE_OUTLINED, "Share flight", on_share))
    if r.departure is not None or r.arrival is not None:
        return ft.Column(
            transport_body(r, on_ticket, secondary, titled),
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            data={"detail": r.reference},
        )
    rows = [
        _row(label, value, opens(open_url, link) if open_url and link else None)
        for label, value, link in _rows(r)
    ]
    listed: list[ft.Control] = []
    for i, row in enumerate(rows):
        if i:
            listed.append(ft.Divider(height=1, thickness=1, color=ft.Colors.OUTLINE_VARIANT))
        listed.append(row)
    return ft.Column(
        [
            *([ft.Text(headline(r), size=26, weight=ft.FontWeight.W_700)] if titled else []),
            *([ft.Row([primary("Show Ticket", on_ticket)])] if on_ticket else []),
            ft.Container(
                ft.Column(listed, spacing=0, tight=True),
                bgcolor=ft.Colors.SURFACE_CONTAINER,
                border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                border_radius=12,
            ),
            *([action_rows(secondary)] if secondary else []),
        ],
        spacing=12,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        data={"detail": r.reference},
    )
