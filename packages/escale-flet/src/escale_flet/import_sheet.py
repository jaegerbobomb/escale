"""The import confirmation sheet (S004, mockup "Import PDF & offline ticket", step 2).

Nothing is saved until the user presses "Add to trip"; a file with nothing recognised
offers "Add manually" instead.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from datetime import datetime
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation, ExtractionResult

Action = Callable[[ft.Event[Any] | None], Awaitable[None] | None]

MAX_WIDTH = 640

_KIND = {
    "TrainReservation": "Train",
    "BusReservation": "Bus",
    "FlightReservation": "Flight",
    "BoatReservation": "Boat",
    "LodgingReservation": "Stay",
    "EventReservation": "Event",
    "FoodEstablishmentReservation": "Restaurant",
    "RentalCarReservation": "Car rental",
    "TaxiReservation": "Taxi",
}
_DAYS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def format_when(moment: datetime) -> str:
    """``Sun 14 Mar 2027 · 08:04``, in the time zone of the place (as printed on tickets)."""
    day = _DAYS[moment.weekday()]
    return f"{day} {moment.day} {_MONTHS[moment.month - 1]} {moment.year} · {moment:%H:%M}"


def headline(reservation: ExtractedReservation) -> str:
    """Train or flight number when known, else the kind of reservation."""
    trip = reservation.raw.get("reservationFor")
    if isinstance(trip, Mapping):
        if isinstance(trip.get("trainNumber"), str):
            return str(trip["trainNumber"])
        if isinstance(trip.get("busNumber"), str):
            return str(trip["busNumber"])
        number = trip.get("flightNumber")
        airline = trip.get("airline")
        if isinstance(number, str):
            code = airline.get("iataCode") if isinstance(airline, Mapping) else None
            return f"{code} {number}" if isinstance(code, str) else number
        name = trip.get("name")
        if isinstance(name, str):
            return name
    return _KIND.get(reservation.type, reservation.type.removesuffix("Reservation"))


def route(reservation: ExtractedReservation) -> str | None:
    dep, arr = reservation.departure, reservation.arrival
    names = [stop.name or stop.code for stop in (dep, arr) if stop is not None]
    return " → ".join(n for n in names if n) or None


def travellers(reservation: ExtractedReservation) -> list[str]:
    under = reservation.raw.get("underName")
    people = under if isinstance(under, list) else [under]
    return [p["name"] for p in people if isinstance(p, Mapping) and isinstance(p.get("name"), str)]


def _row(label: str, value: str) -> ft.Control:
    return ft.Row(
        [
            ft.Text(label, color=ft.Colors.ON_SURFACE_VARIANT),
            ft.Text(value, text_align=ft.TextAlign.RIGHT, expand=True),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )


def _card(reservation: ExtractedReservation) -> ft.Control:
    lines: list[ft.Control] = [
        ft.Text(headline(reservation), theme_style=ft.TextThemeStyle.TITLE_MEDIUM),
    ]
    where = route(reservation)
    if where:
        lines.append(ft.Text(where))
    lines.append(ft.Divider(height=8))
    when = reservation.departure.time if reservation.departure else None
    if when is not None:
        lines.append(_row("Date", format_when(when)))
    names = travellers(reservation)
    if names:
        lines.append(_row("Travellers", ", ".join(names)))
    lines.append(_row("Add to", "New trip"))
    # a card that stands out from the sheet in dark as in light (Adwaita's .card)
    return ft.Container(
        ft.Column(lines, spacing=6),
        padding=16,
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border.all(1, ft.Colors.OUTLINE),
        border_radius=12,
        data={"found": reservation.reference},
    )


def _sheet(title: str, body: list[ft.Control], actions: list[ft.Control]) -> ft.BottomSheet:
    return ft.BottomSheet(
        ft.Container(
            ft.Column(
                [
                    ft.Text(title, theme_style=ft.TextThemeStyle.TITLE_LARGE),
                    *body,
                    ft.Row(actions, alignment=ft.MainAxisAlignment.END),
                ],
                spacing=12,
                tight=True,
                # a long export scrolls instead of being cut (S028)
                scroll=ft.ScrollMode.AUTO,
                data={"sheet_body": True},
            ),
            padding=24,
        ),
        show_drag_handle=True,
        size_constraints=ft.BoxConstraints(max_width=MAX_WIDTH),
    )


def _manual_entry_button() -> ft.Control:
    return ft.Button("Add manually", disabled=True, tooltip="Coming with manual entry")


def confirmation_sheet(
    result: ExtractionResult, on_confirm: Action, on_cancel: Action
) -> ft.BottomSheet:
    """What the import found, to confirm or cancel; or why nothing can be added."""
    name = result.document.name if result.document else "the file"
    cancel = ft.TextButton("Cancel", on_click=on_cancel)
    if result.error is not None:
        return _sheet(
            "Cannot read the file",
            [ft.Text(result.error)],
            [cancel, _manual_entry_button()],
        )
    if result.nothing_recognised:
        return _sheet(
            "Nothing recognised",
            [ft.Text(f"Escale found no reservation in {name}.")],
            [cancel, _manual_entry_button()],
        )
    count = len(result.reservations)
    notes = ["Check before adding: nothing is saved automatically."]
    if result.documents:  # a KDE Itinerary export (S028)
        n = len(result.documents)
        notes.append(f"With {n} document{'s' if n > 1 else ''}.")
    if result.not_imported:
        notes.append(f"Not imported: {', '.join(result.not_imported)}.")
    return _sheet(
        "Reservation found" if count == 1 else f"{count} reservations found",
        [
            *(ft.Text(n, color=ft.Colors.ON_SURFACE_VARIANT) for n in notes),
            *(_card(r) for r in result.reservations),
        ],
        [cancel, ft.FilledButton("Add to trip", on_click=on_confirm)],
    )


def phone_sheet(on_close: Action) -> ft.BottomSheet:
    """Import on Android or iOS: extraction runs on Linux only (ADR-0003)."""
    return _sheet(
        "Import on your computer",
        [
            ft.Text(
                "Escale reads tickets on Linux. Import the file there: the reservation "
                "reaches this device through the sync."
            )
        ],
        [ft.FilledButton("OK", on_click=on_close)],
    )
