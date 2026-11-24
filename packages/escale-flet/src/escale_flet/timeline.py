"""The current trip as a timeline of "detailed" cards (S010b, mockup "Voyage en cours").

Each card carries ``data={"segment": <reference>, "next": <bool>}`` so that tests and
later stories (jump index, detail) can find it.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
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


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


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


def _dim(text: str) -> ft.Text:
    return ft.Text(text, opacity=0.7)


def _stop_row(time: datetime | None, name: str | None, extra: str | None) -> ft.Control:
    return ft.Row(
        [
            ft.Text(
                f"{time:%H:%M}" if time else "--:--",
                theme_style=ft.TextThemeStyle.TITLE_MEDIUM,
                width=56,
            ),
            ft.Text(name or "?", expand=True),
            *([_dim(extra)] if extra else []),
        ]
    )


def _transport_lines(r: ExtractedReservation) -> list[ft.Control]:
    trip = _m(r.raw.get("reservationFor"))
    platform = trip.get("departurePlatform")
    lines: list[ft.Control] = [
        _stop_row(
            r.departure.time if r.departure else None,
            r.departure.name if r.departure else None,
            f"Platform {platform}" if isinstance(platform, str) else None,
        ),
        _stop_row(
            r.arrival.time if r.arrival else None,
            r.arrival.name if r.arrival else None,
            None,
        ),
    ]
    facts: list[str] = []
    seat = _m(_m(r.raw.get("reservedTicket")).get("ticketedSeat"))
    coach, number = seat.get("seatSection"), seat.get("seatNumber")
    if isinstance(coach, str) and isinstance(number, str):
        facts.append(f"Coach {coach} · Seat {number}")
    if r.departure and r.arrival and r.departure.time and r.arrival.time:
        facts.append(duration(r.arrival.time - r.departure.time))
    if facts:
        lines.append(_dim(" · ".join(facts)))
    return lines


def _lodging_lines(r: ExtractedReservation, start: datetime, end: datetime) -> list[ft.Control]:
    place = _m(r.raw.get("reservationFor"))
    street = _m(place.get("address")).get("streetAddress")
    nights = max((end.date() - start.date()).days, 1)
    return [
        *([_dim(street)] if isinstance(street, str) else []),
        _dim(f"{nights} night{'s' if nights > 1 else ''}"),
        ft.Text(f"Check-in {_day(start)} · {start:%H:%M}"),
        ft.Text(f"Check-out {_day(end)} · {end:%H:%M}"),
    ]


def _other_lines(r: ExtractedReservation, start: datetime) -> list[ft.Control]:
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


OnTicket = Callable[[ExtractedReservation], Any]


def segment_card(
    r: ExtractedReservation, now: datetime, is_next: bool, on_ticket: OnTicket | None = None
) -> ft.Control:
    start, end = span(r) or (now, now)
    lines: list[ft.Control] = []
    if is_next:
        wait = start - now
        lines.append(
            ft.Text(
                f"Next · leaves in {duration(wait)}" if wait > timedelta(0) else "Next · now",
                color=ft.Colors.PRIMARY,
                theme_style=ft.TextThemeStyle.LABEL_LARGE,
            )
        )
    lines.append(ft.Text(_title(r), theme_style=ft.TextThemeStyle.TITLE_MEDIUM))
    if r.type in _TRANSPORT:
        lines += _transport_lines(r)
    elif r.type == "LodgingReservation":
        lines += _lodging_lines(r, start, end)
    else:
        lines += _other_lines(r, start)
    if on_ticket is not None and (ticket_of(r).barcode is not None or r.subject_of):
        lines.append(
            ft.Row(
                [
                    ft.TextButton(
                        "Ticket",
                        icon=ft.Icons.CONFIRMATION_NUMBER_OUTLINED,
                        on_click=lambda _: on_ticket(r),
                    )
                ],
                alignment=ft.MainAxisAlignment.END,
            )
        )
    return ft.Container(
        ft.Column(lines, spacing=6, tight=True),
        padding=16,
        border_radius=12,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border.all(2, ft.Colors.PRIMARY) if is_next else None,
        data={"segment": r.reference or headline(r), "next": is_next},
    )


def next_segment(trip: Trip, now: datetime) -> ExtractedReservation | None:
    """The first reservation not finished yet."""
    for r in trip.reservations:
        timing = span(r)
        if timing is not None and timing[1] >= now:
            return r
    return None


def trip_view(trip: Trip, now: datetime, on_ticket: OnTicket | None = None) -> ft.Control:
    names: list[str] = []
    for r in trip.reservations:
        for name in travellers(r):
            if name not in names:
                names.append(name)
    upcoming = next_segment(trip, now)
    header: list[ft.Control] = [
        ft.Text(trip.name, theme_style=ft.TextThemeStyle.HEADLINE_SMALL),
        _dim(date_range(trip.start, trip.end)),
    ]
    if names:
        header.append(_dim(", ".join(names)))
    return ft.ListView(
        [
            ft.Column(header, spacing=2),
            *(segment_card(r, now, r is upcoming, on_ticket) for r in trip.reservations),
        ],
        spacing=12,
        padding=ft.Padding.symmetric(vertical=8),
        expand=True,
    )
