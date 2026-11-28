"""The stay editor (S017b): KDE Itinerary's ``HotelEditor`` fields, in an action dialog."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation
from escale_core.stays import StayFields, fields_of, problems
from escale_flet.editor import EditorKind, action_editor

OnSave = Callable[[StayFields], Awaitable[None]]

_GROUPS: tuple[tuple[str, tuple[tuple[str, str, str], ...]], ...] = (
    ("Hotel", (("name", "Name", ""),)),
    (
        "Address",
        (
            ("street", "Street", ""),
            ("postal_code", "Postal code", ""),
            ("city", "City", ""),
            ("region", "Region", ""),
            ("country", "Country", ""),
            ("latitude", "Latitude", "51.5174"),
            ("longitude", "Longitude", "-0.1137"),
        ),
    ),
    (
        "Stay",
        (
            ("check_in_date", "Check-in date", "YYYY-MM-DD"),
            ("check_in_time", "Check-in time", "HH:MM"),
            ("check_out_date", "Check-out date", "YYYY-MM-DD"),
            ("check_out_time", "Check-out time", "HH:MM"),
            ("description", "Room", ""),
        ),
    ),
    (
        "Contact",
        (
            ("telephone", "Telephone", ""),
            ("email", "E-mail", ""),
            ("website", "Website", "https://"),
        ),
    ),
    ("Booking", (("reference", "Booking reference", ""), ("under_name", "Under the name of", ""))),
)

STAY = EditorKind("Edit Stay", _GROUPS, fields_of, problems)


def stay_editor(
    r: ExtractedReservation,
    on_save: OnSave,
    on_cancel: Callable[[Any], Any],
    on_dismiss: Callable[[Any], Any],
    sheet: bool = False,
    height: float = 640,
    initial: StayFields | None = None,
) -> ft.AlertDialog | ft.BottomSheet:
    return action_editor(STAY, r, on_save, on_cancel, on_dismiss, sheet, height, initial)
