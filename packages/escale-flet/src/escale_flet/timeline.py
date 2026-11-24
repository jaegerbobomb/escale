"""The current trip as a timeline (S010b; look from the mockup "Voyage en cours", S020).

The next segment is an accented card with a "NEXT" band; the others sit in boxed lists
(rounded blocks with 1 px separators), as in libadwaita. Each segment carries
``data={"segment": <reference>, "next": <bool>}`` for tests and later stories.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation
from escale_core.tickets import ticket_of
from escale_core.trips import Trip, span
from escale_flet.import_sheet import headline, travellers

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_TRANSPORT = {"TrainReservation", "FlightReservation", "BusReservation", "BoatReservation"}
MAX_WIDTH = 720

CARD_RADIUS = 14
LIST_RADIUS = 12
CONNECTION_MAX = timedelta(hours=6)
"""Two legs closer than this, arriving and leaving at the same place, are a connection."""

_ICONS = {
    "TrainReservation": ft.Icons.TRAIN_OUTLINED,
    "FlightReservation": ft.Icons.FLIGHT,
    "BusReservation": ft.Icons.DIRECTIONS_BUS_OUTLINED,
    "BoatReservation": ft.Icons.DIRECTIONS_BOAT_OUTLINED,
    "LodgingReservation": ft.Icons.HOTEL_OUTLINED,
    "FoodEstablishmentReservation": ft.Icons.RESTAURANT_OUTLINED,
    "EventReservation": ft.Icons.LOCAL_ACTIVITY_OUTLINED,
}

OnTicket = Callable[[ExtractedReservation], Any]


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


# --- text helpers ---


def date_range(start: datetime, end: datetime) -> str:
    """``8–10 Jul 2026``, ``30 Jun – 2 Jul 2026``, ``8 Jul 2026``."""
    if start.date() == end.date():
        return f"{start.day} {_MONTHS[start.month - 1]} {start.year}"
    if (start.month, start.year) == (end.month, end.year):
        return f"{start.day}–{end.day} {_MONTHS[end.month - 1]} {end.year}"
    return f"{start.day} {_MONTHS[start.month - 1]} – {end.day} {_MONTHS[end.month - 1]} {end.year}"


def duration(delta: timedelta) -> str:
    minutes = int(delta.total_seconds() // 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d}" if hours else f"{minutes} min"


def _day(moment: datetime) -> str:
    return f"{_DAYS[moment.weekday()]} {moment.day} {_MONTHS[moment.month - 1]}"


def initials(name: str) -> str:
    parts = [p for p in name.replace("-", " ").split() if p]
    return "".join(p[0] for p in parts[:2]).upper() or "?"


# --- small widgets (libadwaita-like) ---


def _dim(text: str, size: float = 12.5) -> ft.Text:
    return ft.Text(text, size=size, color=ft.Colors.ON_SURFACE_VARIANT)


def _strong(text: str, size: float = 15) -> ft.Text:
    return ft.Text(text, size=size, weight=ft.FontWeight.W_700)


def chip(text: str, tone: str = "neutral") -> ft.Control:
    """A pill badge: neutral, success (confirmed, on time) or accent."""
    colours = {
        "neutral": (ft.Colors.with_opacity(0.07, ft.Colors.ON_SURFACE), ft.Colors.ON_SURFACE),
        "success": (ft.Colors.with_opacity(0.15, ft.Colors.TERTIARY), ft.Colors.TERTIARY),
        "accent": (ft.Colors.with_opacity(0.15, ft.Colors.PRIMARY), ft.Colors.PRIMARY),
    }
    bg, fg = colours[tone]
    return ft.Container(
        ft.Text(text, size=12, weight=ft.FontWeight.W_700, color=fg),
        bgcolor=bg,
        padding=ft.Padding.symmetric(horizontal=10, vertical=4),
        border_radius=12,
        data={"chip": text},
    )


def _chips(items: Sequence[ft.Control]) -> ft.Control:
    return ft.Row(list(items), spacing=7, wrap=True, run_spacing=7)


def _avatar(name: str, index: int) -> ft.Control:
    return ft.Container(
        ft.Text(initials(name), size=12, weight=ft.FontWeight.W_700, color=ft.Colors.ON_PRIMARY),
        width=30,
        height=30,
        border_radius=15,
        bgcolor=ft.Colors.PRIMARY,
        alignment=ft.Alignment.CENTER,
        border=ft.Border.all(2, ft.Colors.SURFACE),
        tooltip=name,
        margin=ft.Margin.only(left=0 if index == 0 else -8),
        data={"avatar": name},
    )


# --- segment rows ---


def _stop(time: datetime | None, name: str | None, platform: str | None) -> ft.Control:
    return ft.Row(
        [
            ft.Text(
                f"{time:%H:%M}" if time else "--:--",
                size=26,
                weight=ft.FontWeight.W_700,
                width=86,
            ),
            ft.Text(name or "?", size=15, expand=True),
            *([chip(f"Platform {platform}")] if platform else []),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _transport(r: ExtractedReservation) -> list[ft.Control]:
    trip = _m(r.raw.get("reservationFor"))
    dep_platform = trip.get("departurePlatform")
    arr_platform = trip.get("arrivalPlatform")
    lines: list[ft.Control] = [
        _stop(
            r.departure.time if r.departure else None,
            r.departure.name if r.departure else None,
            dep_platform if isinstance(dep_platform, str) else None,
        ),
        ft.Container(width=2, height=14, bgcolor=ft.Colors.OUTLINE, margin=ft.Margin.only(left=26)),
        _stop(
            r.arrival.time if r.arrival else None,
            r.arrival.name if r.arrival else None,
            arr_platform if isinstance(arr_platform, str) else None,
        ),
    ]
    facts: list[ft.Control] = []
    seat = _m(_m(r.raw.get("reservedTicket")).get("ticketedSeat"))
    coach, number, seat_class = (
        seat.get("seatSection"),
        seat.get("seatNumber"),
        seat.get("seatingType"),
    )
    if isinstance(coach, str) and isinstance(number, str):
        facts.append(chip(f"Coach {coach} · Seat {number}"))
    if isinstance(seat_class, str):
        facts.append(chip(f"Class {seat_class}"))
    if r.departure and r.arrival and r.departure.time and r.arrival.time:
        facts.append(_dim(duration(r.arrival.time - r.departure.time), 13))
    if facts:
        lines.append(ft.Container(_chips(facts), margin=ft.Margin.only(top=6)))
    return lines


def _confirmed(r: ExtractedReservation) -> bool:
    status = r.raw.get("reservationStatus")
    return isinstance(status, str) and status.endswith("ReservationConfirmed")


def _lodging(r: ExtractedReservation, start: datetime, end: datetime) -> list[ft.Control]:
    place = _m(r.raw.get("reservationFor"))
    street = _m(place.get("address")).get("streetAddress")
    nights = max((end.date() - start.date()).days, 1)
    badges = [chip(f"{nights} night{'s' if nights > 1 else ''}")]
    if _confirmed(r):
        badges.append(chip("Confirmed", "success"))
    return [
        *([_dim(street)] if isinstance(street, str) else []),
        ft.Container(_chips(badges), margin=ft.Margin.only(top=4)),
        ft.Row(
            [
                ft.Column(
                    [_dim("Check-in"), ft.Text(f"{_day(start)} · {start:%H:%M}")],
                    spacing=1,
                    expand=True,
                ),
                ft.Column(
                    [_dim("Check-out"), ft.Text(f"{_day(end)} · {end:%H:%M}")],
                    spacing=1,
                    expand=True,
                ),
            ],
        ),
    ]


def _other(r: ExtractedReservation, start: datetime) -> list[ft.Control]:
    target = _m(r.raw.get("reservationFor"))
    location = _m(target.get("location")) or target
    name = location.get("name")
    return [
        ft.Text(f"{_day(start)} · {start:%H:%M}"),
        *([_dim(name)] if isinstance(name, str) else []),
    ]


def _title(r: ExtractedReservation) -> str:
    if r.type == "LodgingReservation":
        name = _m(r.raw.get("reservationFor")).get("name")
        if isinstance(name, str):
            return name
    return headline(r)


def has_ticket(r: ExtractedReservation) -> bool:
    """Something to show full screen: a barcode, or a kept document (S015)."""
    return ticket_of(r).barcode is not None or bool(r.subject_of)


def _segment_body(r: ExtractedReservation, now: datetime, on_ticket: OnTicket | None) -> ft.Control:
    start, end = span(r) or (now, now)
    title_row: list[ft.Control] = [
        ft.Icon(
            _ICONS.get(r.type, ft.Icons.EVENT_NOTE_OUTLINED),
            size=20,
            color=ft.Colors.ON_SURFACE_VARIANT,
        ),
        ft.Container(_strong(_title(r)), expand=True),
    ]
    if on_ticket is not None and has_ticket(r):
        title_row.append(
            ft.TextButton(
                "Ticket",
                icon=ft.Icons.CONFIRMATION_NUMBER_OUTLINED,
                on_click=lambda _: on_ticket(r),
            )
        )
    lines: list[ft.Control] = [ft.Row(title_row, vertical_alignment=ft.CrossAxisAlignment.CENTER)]
    if r.type in _TRANSPORT:
        lines += _transport(r)
    elif r.type == "LodgingReservation":
        lines += _lodging(r, start, end)
    else:
        lines += _other(r, start)
    return ft.Column(lines, spacing=4, tight=True)


def segment_card(
    r: ExtractedReservation, now: datetime, is_next: bool, on_ticket: OnTicket | None = None
) -> ft.Control:
    """One segment: the accented "next" card, or a row of a boxed list."""
    body = _segment_body(r, now, on_ticket)
    data = {"segment": r.reference or headline(r), "next": is_next}
    if not is_next:
        return ft.Container(
            body, padding=ft.Padding.symmetric(horizontal=16, vertical=14), data=data
        )
    start, _ = span(r) or (now, now)
    wait = start - now
    band = "NEXT · " + (f"leaves in {duration(wait)}" if wait > timedelta(0) else "now")
    return ft.Container(
        ft.Column(
            [
                ft.Container(
                    ft.Text(band, size=12, weight=ft.FontWeight.W_700, color=ft.Colors.ON_PRIMARY),
                    bgcolor=ft.Colors.PRIMARY,
                    padding=ft.Padding.symmetric(horizontal=16, vertical=7),
                ),
                ft.Container(body, padding=16),
            ],
            spacing=0,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border.all(2, ft.Colors.PRIMARY),
        border_radius=CARD_RADIUS,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        shadow=ft.BoxShadow(
            blur_radius=20,
            offset=ft.Offset(0, 6),
            color=ft.Colors.with_opacity(0.18, ft.Colors.PRIMARY),
        ),
        data=data,
    )


def _boxed(rows: Sequence[ft.Control]) -> ft.Control:
    """libadwaita's ``.boxed-list``: one rounded block, rows split by 1 px lines."""
    items: list[ft.Control] = []
    for i, row in enumerate(rows):
        if i:
            items.append(ft.Divider(height=1, thickness=1, color=ft.Colors.OUTLINE_VARIANT))
        items.append(row)
    return ft.Container(
        ft.Column(items, spacing=0, tight=True),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=LIST_RADIUS,
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
    )


def connection(previous: ExtractedReservation, following: ExtractedReservation) -> str | None:
    """``Connection of 20 min at Bruxelles-Midi`` between two legs, if they connect."""
    if previous.type not in _TRANSPORT or following.type not in _TRANSPORT:
        return None
    if not (
        previous.arrival
        and following.departure
        and previous.arrival.time
        and following.departure.time
    ):
        return None
    if previous.arrival.name != following.departure.name:
        return None
    gap = following.departure.time - previous.arrival.time
    if gap < timedelta(0) or gap > CONNECTION_MAX:
        return None
    return f"Connection of {duration(gap)} at {previous.arrival.name}"


def _connection_row(text: str) -> ft.Control:
    return ft.Container(
        ft.Row(
            [
                ft.Icon(
                    ft.Icons.TRANSFER_WITHIN_A_STATION, size=18, color=ft.Colors.ON_SURFACE_VARIANT
                ),
                _dim(text, 13),
            ],
            spacing=9,
        ),
        padding=ft.Padding.symmetric(horizontal=16, vertical=4),
        data={"connection": text},
    )


def next_segment(trip: Trip, now: datetime) -> ExtractedReservation | None:
    """The first reservation not finished yet."""
    for r in trip.reservations:
        timing = span(r)
        if timing is not None and timing[1] >= now:
            return r
    return None


def _header(trip: Trip) -> ft.Control:
    names: list[str] = []
    for r in trip.reservations:
        for name in travellers(r):
            if name not in names:
                names.append(name)
    caption = [date_range(trip.start, trip.end)]
    if names:
        caption.append(f"{len(names)} traveller{'s' if len(names) > 1 else ''}")
    texts = ft.Column(
        [ft.Text(trip.name, size=26, weight=ft.FontWeight.W_700), _dim(" · ".join(caption), 13)],
        spacing=2,
        expand=True,
    )
    avatars = ft.Row([_avatar(n, i) for i, n in enumerate(names[:4])], spacing=0)
    return ft.Row([texts, avatars], vertical_alignment=ft.CrossAxisAlignment.CENTER)


def trip_view(trip: Trip, now: datetime, on_ticket: OnTicket | None = None) -> ft.Control:
    upcoming = next_segment(trip, now)
    blocks: list[ft.Control] = [_header(trip)]
    pending: list[ft.Control] = []

    def flush() -> None:
        if pending:
            blocks.append(_boxed(list(pending)))
            pending.clear()

    previous: ExtractedReservation | None = None
    for r in trip.reservations:
        link = connection(previous, r) if previous is not None else None
        if r is upcoming:
            flush()
            if link:
                blocks.append(_connection_row(link))
            blocks.append(segment_card(r, now, True, on_ticket))
        else:
            if link:
                flush()
                blocks.append(_connection_row(link))
            pending.append(segment_card(r, now, False, on_ticket))
        previous = r
    flush()
    return ft.ListView(blocks, spacing=12, padding=ft.Padding.symmetric(vertical=8), expand=True)
