"""A train's, flight's, bus's or boat's detail, as the mockup's "Trajet en train" (S062).

Identity (icon, number, kind or operator), a timeline card with the two times large and
the stations or airports, the seat as chips, the booking's facts as rows, then "Show
Ticket" wide at the bottom with the other actions as rows (ADR-0008).
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation, Stop
from escale_flet.import_sheet import headline, travellers
from escale_flet.stay_view import TINT, Action, action_rows, card, fact, facts
from escale_flet.timeline import chip, duration

_KINDS = {
    "TrainReservation": ("Train", ft.Icons.TRAIN_OUTLINED),
    "FlightReservation": ("Flight", ft.Icons.FLIGHT),
    "BusReservation": ("Bus", ft.Icons.DIRECTIONS_BUS_OUTLINED),
    "BoatReservation": ("Boat", ft.Icons.DIRECTIONS_BOAT_OUTLINED),
}
_WHERE = {
    "departure": ("departurePlatform", "departureTerminal", "departureGate"),
    "arrival": ("arrivalPlatform", "arrivalTerminal", "arrivalGate"),
}


def _m(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _operator(r: ExtractedReservation) -> str:
    trip = _m(r.raw.get("reservationFor"))
    kind = _KINDS.get(r.type, ("Trip", None))[0]
    name = _text(_m(trip.get("airline")).get("name")) or _text(_m(trip.get("provider")).get("name"))
    return f"{kind} · {name}" if name else kind


def _identity(r: ExtractedReservation, titled: bool) -> ft.Control:
    icon = _KINDS.get(r.type, ("", ft.Icons.EVENT_NOTE_OUTLINED))[1]
    lines: list[ft.Control] = []
    if titled:
        lines.append(ft.Text(headline(r), size=22, weight=ft.FontWeight.W_700))
    lines.append(ft.Text(_operator(r), size=13, color=ft.Colors.ON_SURFACE_VARIANT))
    return ft.Row(
        [
            ft.Container(
                ft.Icon(icon, size=22, color=ft.Colors.PRIMARY),
                width=42,
                height=42,
                border_radius=11,
                bgcolor=TINT,
                alignment=ft.Alignment.CENTER,
            ),
            ft.Column(lines, spacing=2, tight=True, expand=True),
        ],
        spacing=12,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def _zone(moment: datetime) -> str:
    """``CEST`` for a named zone, else ``UTC+2`` from the offset."""
    name = moment.tzname()
    offset = moment.utcoffset()
    if name and not name.startswith("UTC") and offset is not None and name != "UTC":
        return name
    if offset is None:
        return ""
    minutes = int(offset.total_seconds() // 60)
    sign = "+" if minutes >= 0 else "-"
    hours, rest = divmod(abs(minutes), 60)
    return f"UTC{sign}{hours}" + (f":{rest:02d}" if rest else "")


def _stop(r: ExtractedReservation, end: str, stop: Stop, zones: bool, last: bool) -> ft.Control:
    trip = _m(r.raw.get("reservationFor"))
    platform, terminal, gate = (_text(trip.get(k)) for k in _WHERE[end])
    where = [
        f"Platform {platform}" if platform else None,
        f"Terminal {terminal}" if terminal else None,
        f"Gate {gate}" if gate else None,
    ]
    time_column: list[ft.Control] = []
    if stop.time is not None:
        time_column.append(ft.Text(f"{stop.time:%H:%M}", size=22, weight=ft.FontWeight.W_700))
        if zones:
            time_column.append(
                ft.Text(_zone(stop.time), size=11, color=ft.Colors.ON_SURFACE_VARIANT)
            )
    dot = ft.Container(
        width=11,
        height=11,
        border_radius=6,
        bgcolor=ft.Colors.PRIMARY if last else None,
        border=None if last else ft.Border.all(2.5, ft.Colors.PRIMARY),
        margin=ft.Margin.only(top=8),
    )
    return ft.Row(
        [
            ft.Container(
                ft.Column(
                    time_column,
                    spacing=0,
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.END,
                ),
                width=64,
            ),
            dot,
            ft.Column(
                [
                    ft.Text(stop.name or stop.code or "", size=15.5, weight=ft.FontWeight.W_700),
                    *(
                        [
                            ft.Text(
                                " · ".join(w for w in where if w),
                                size=12.5,
                                color=ft.Colors.ON_SURFACE_VARIANT,
                            )
                        ]
                        if any(where)
                        else []
                    ),
                ],
                spacing=2,
                tight=True,
                expand=True,
            ),
        ],
        spacing=14,
        vertical_alignment=ft.CrossAxisAlignment.START,
        data={"stop": end},
    )


def _journey(r: ExtractedReservation) -> ft.Control:
    dep, arr = r.departure, r.arrival
    times = [s.time for s in (dep, arr) if s is not None and s.time is not None]
    zones = len(times) == 2 and times[0].utcoffset() != times[1].utcoffset()
    rows: list[ft.Control] = []
    if dep is not None:
        rows.append(_stop(r, "departure", dep, zones, last=False))
    if dep and arr and dep.time and arr.time:
        rows.append(
            ft.Container(
                ft.Row([chip(duration(arr.time - dep.time))]),
                padding=ft.Padding.only(left=64 + 14 + 11 + 14, top=4, bottom=4),
                border=ft.Border.only(left=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)),
                margin=ft.Margin.only(left=64 + 14 + 4),
            )
        )
    if arr is not None:
        rows.append(_stop(r, "arrival", arr, zones, last=True))
    return card(ft.Container(ft.Column(rows, spacing=6, tight=True), padding=18))


def _chips(r: ExtractedReservation) -> list[ft.Control]:
    seat = _m(_m(r.raw.get("reservedTicket")).get("ticketedSeat"))
    coach, number = _text(seat.get("seatSection")), _text(seat.get("seatNumber"))
    found: list[ft.Control] = []
    place = " · ".join(
        p for p in (f"Coach {coach}" if coach else None, f"Seat {number}" if number else None) if p
    )
    if place:
        found.append(chip(place))
    seat_class = _text(seat.get("seatingType")) or _text(r.raw.get("airplaneSeatClass"))
    if seat_class:
        found.append(chip(f"Class {seat_class}"))
    return [ft.Row(found, spacing=8, wrap=True, run_spacing=8)] if found else []


def transport_body(
    r: ExtractedReservation,
    on_ticket: Action | None,
    secondary: list[tuple[ft.IconData, str, Action]],
    titled: bool = True,
) -> list[ft.Control]:
    """Everything under the header bar of a transport's detail."""
    body: list[ft.Control] = [_identity(r, titled), _journey(r), *_chips(r)]
    booking: list[ft.Control] = []
    if r.reference:
        booking.append(
            fact(ft.Icons.CONFIRMATION_NUMBER_OUTLINED, "Booking reference", r.reference)
        )
    names = travellers(r)
    if names:
        booking.append(fact(ft.Icons.PERSON_OUTLINE, "Travellers", ", ".join(names)))
    if booking:
        body.append(facts(booking))
    if on_ticket is not None:
        body.append(
            ft.Row(
                [
                    ft.FilledButton(
                        "Show Ticket",
                        on_click=on_ticket,
                        expand=True,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            padding=ft.Padding.symmetric(vertical=16),
                        ),
                    )
                ]
            )
        )
    if secondary:
        body.append(action_rows(secondary))
    return body
