"""The stay editor (S017b), as a GNOME action dialog (S061, ADR-0008).

KDE Itinerary's ``HotelEditor`` fields, as entry rows in boxed lists, one list per
section. The header holds "Cancel", the heading and "Save" (suggested), insensitive
with the reasons below the form while the fields are not valid. Return saves, Esc
cancels; under 550 px the dialog fills the window.
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
WIDTH = 560


def _entry_row(field: ft.TextField) -> ft.Control:
    return ft.Container(field, padding=ft.Padding.symmetric(horizontal=16, vertical=2))


def stay_editor(
    r: ExtractedReservation,
    on_save: OnSave,
    on_cancel: Callable[[Any], Any],
    on_dismiss: Callable[[Any], Any],
    full_window: float | None = None,
    height: float = 640,
    initial: StayFields | None = None,
) -> ft.AlertDialog:
    """The dialog; ``full_window`` is the window's width when it should fill it.
    ``data["values"]`` gives the fields as typed so far."""
    inputs: dict[str, ft.TextField] = {}
    save = ft.FilledButton("Save")
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
    values = initial or fields_of(r)
    assert {f.name for f in fields(StayFields)} == {n for _, g in _GROUPS for n, _, _ in g}
    groups: list[ft.Control] = []
    for title, group in _GROUPS:
        rows: list[ft.Control] = []
        for name, label, hint in group:
            field = ft.TextField(
                label=label,
                value=getattr(values, name),
                hint_text=hint or None,
                border=ft.NoInputBorder(),
                on_change=check,
                on_submit=do_save,
                data={"field": name},
            )
            inputs[name] = field
            if rows:
                rows.append(ft.Divider(height=1, thickness=1, color=ft.Colors.OUTLINE_VARIANT))
            rows.append(_entry_row(field))
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
                        ft.Column(rows, spacing=0, tight=True),
                        bgcolor=ft.Colors.SURFACE_CONTAINER,
                        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
                        border_radius=12,
                    ),
                ],
                spacing=6,
                tight=True,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            )
        )
    check()
    return ft.AlertDialog(
        modal=False,
        title=ft.Row(
            [
                ft.TextButton("Cancel", on_click=on_cancel),
                ft.Text(
                    "Edit Stay",
                    size=17,
                    weight=ft.FontWeight.W_700,
                    expand=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                save,
            ],
        ),
        content=ft.Container(
            ft.Column([*groups, errors], spacing=18, scroll=ft.ScrollMode.AUTO),
            width=full_window or WIDTH,
            height=None if full_window else height,
            expand=bool(full_window),
        ),
        inset_padding=ft.Padding.all(0) if full_window else None,
        shape=ft.RoundedRectangleBorder(radius=0 if full_window else 14),
        on_dismiss=on_dismiss,
        data={"editor": r.reference, "values": current},
    )
