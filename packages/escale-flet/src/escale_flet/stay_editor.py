"""The stay editor (S017b): KDE Itinerary's ``HotelEditor`` fields, in groups.

"Save" stays disabled, with the reason below the form, while the fields are not valid.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import fields, replace
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation
from escale_core.stays import StayFields, fields_of, problems

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
_PAIRED = {"postal_code", "check_in_date", "check_out_date", "latitude"}
"""Fields shown side by side with the next one."""


def stay_editor(
    r: ExtractedReservation, on_save: OnSave, on_cancel: Callable[[Any], Any]
) -> ft.Control:
    inputs: dict[str, ft.TextField] = {}
    save = ft.FilledButton("Save", icon=ft.Icons.CHECK)
    errors = ft.Column(spacing=2, tight=True)

    def current() -> StayFields:
        return replace(fields_of(r), **{name: field.value or "" for name, field in inputs.items()})

    def check(_: Any = None) -> None:
        found = problems(current(), r)
        save.disabled = bool(found)
        errors.controls = [ft.Text(p, size=13, color=ft.Colors.ERROR) for p in found]
        try:
            save.update()
            errors.update()
        except (RuntimeError, AssertionError):
            pass  # not on a page yet

    async def do_save(_: Any) -> None:
        if not problems(current(), r):
            await on_save(current())

    save.on_click = do_save
    values = fields_of(r)
    assert {f.name for f in fields(StayFields)} == {n for _, g in _GROUPS for n, _, _ in g}
    groups: list[ft.Control] = []
    for title, group in _GROUPS:
        rows: list[ft.Control] = []
        pending: list[ft.Control] = []
        for name, label, hint in group:
            field = ft.TextField(
                label=label,
                value=getattr(values, name),
                hint_text=hint or None,
                dense=True,
                expand=True,
                on_change=check,
                data={"field": name},
            )
            inputs[name] = field
            pending.append(field)
            if name not in _PAIRED:
                rows.append(ft.Row(pending, spacing=10))
                pending = []
        groups.append(
            ft.Column(
                [
                    ft.Text(
                        title,
                        size=13,
                        weight=ft.FontWeight.W_700,
                        color=ft.Colors.ON_SURFACE_VARIANT,
                    ),
                    ft.Container(
                        ft.Column(rows, spacing=10, tight=True),
                        padding=14,
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        border_radius=14,
                    ),
                ],
                spacing=6,
                tight=True,
            )
        )
    check()
    return ft.Column(
        [
            ft.Row(
                [
                    ft.TextButton("Cancel", on_click=on_cancel),
                    ft.Text(
                        "Edit stay",
                        size=17,
                        weight=ft.FontWeight.W_700,
                        expand=True,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    save,
                ],
            ),
            *groups,
            errors,
        ],
        spacing=14,
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        data={"editor": r.reference},
    )
