"""Action dialogs that edit a booking (S017b, S029a), as GNOME action dialogs (S061,
ADR-0008).

The fields of KDE Itinerary's editor for that kind of booking, as entry rows in boxed
lists, one list per section. The header holds "Cancel", the heading and "Save"
(suggested), insensitive with the reasons below the form while the fields are not
valid. Return saves, Esc cancels. Under 450 px it is a bottom sheet, closed by Cancel or
by swiping it down, as libadwaita's AdwDialog in its automatic presentation mode.

A date or time field (hint ``DATE`` or ``TIME``) ends with a button that opens a date or
a 24-hour time picker; typing still works.
"""

from __future__ import annotations

import contextlib
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, fields, replace
from datetime import datetime, time
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation

Groups = Sequence[tuple[str, Sequence[tuple[str, str, str]]]]
"""Sections: title, then (field, label, hint) rows."""
WIDTH = 560
DATE = "YYYY-MM-DD"
TIME = "HH:MM"
"""Hints of the fields that get a date or a time picker."""


@dataclass(frozen=True)
class EditorKind[F]:
    """What an editor edits: its heading, its sections, and the core's functions."""

    title: str
    groups: Groups
    read: Callable[[ExtractedReservation], F]
    problems: Callable[[F, ExtractedReservation], list[str]]


def _entry_row(field: ft.TextField) -> ft.Control:
    return ft.Container(field, padding=ft.Padding.symmetric(horizontal=16, vertical=2))


def _picker_button(
    name: str,
    hint: str,
    field: ft.TextField,
    check: Callable[[], None],
    show: Callable[[ft.DialogControl], None],
) -> ft.IconButton:
    def filled() -> None:
        check()
        with contextlib.suppress(RuntimeError, AssertionError):  # not on a page
            field.update()

    return ft.IconButton(
        ft.Icons.CALENDAR_MONTH_OUTLINED if hint == DATE else ft.Icons.SCHEDULE,
        tooltip="Choose a date" if hint == DATE else "Choose a time",
        on_click=lambda _: show(_picker(hint, field, filled)),
        data={"picker": name},
    )


def _parsed(value: str, form: str) -> datetime | None:
    try:
        return datetime.strptime(value.strip(), form)
    except ValueError:
        return None


def _picker(
    hint: str, field: ft.TextField, filled: Callable[[], None]
) -> ft.DatePicker | ft.TimePicker:
    """The picker for a date or time field, on its value; a pick fills it in."""
    if hint == DATE:
        day = ft.DatePicker(
            value=_parsed(field.value or "", "%Y-%m-%d"),
            first_date=datetime(1900, 1, 1),
            last_date=datetime(2100, 12, 31),
        )

        def picked_day(_: Any) -> None:
            picked = day.value
            if isinstance(picked, datetime) and picked.tzinfo is not None:
                picked = picked.astimezone()  # Flutter sends the day's local midnight in UTC
            if picked is not None:
                field.value = f"{picked:%Y-%m-%d}"
                filled()

        day.on_change = picked_day
        return day
    start = _parsed(field.value or "", "%H:%M")
    clock = ft.TimePicker(
        value=start.time() if start else time(12, 0),
        hour_format=ft.TimePickerHourFormat.H24,
    )

    def picked_time(_: Any) -> None:
        if clock.value is not None:
            field.value = f"{clock.value:%H:%M}"
            filled()

    clock.on_change = picked_time
    return clock


def action_editor[F](
    kind: EditorKind[F],
    r: ExtractedReservation,
    on_save: Callable[[F], Awaitable[None]],
    on_cancel: Callable[[Any], Any],
    on_dismiss: Callable[[Any], Any],
    sheet: bool = False,
    height: float = 640,
    initial: F | None = None,
    show: Callable[[ft.DialogControl], None] | None = None,
    note: str | None = None,
) -> ft.AlertDialog | ft.BottomSheet:
    """A floating dialog, or a bottom sheet on a phone (``sheet``), as libadwaita's
    AdwDialog presents itself. ``data["values"]`` gives the fields as typed so far;
    ``show`` puts a date or time picker above it (no picker buttons without it);
    ``note`` is a line above the form (the file a new booking keeps, S064)."""
    inputs: dict[str, ft.TextField] = {}
    save = ft.FilledButton("Save")
    errors = ft.Column(spacing=2, tight=True)

    def current() -> F:
        typed = {name: field.value or "" for name, field in inputs.items()}
        return replace(kind.read(r), **typed)  # type: ignore[type-var]

    def check(_: Any = None) -> None:
        found = kind.problems(current(), r)
        save.disabled = bool(found)
        errors.controls = [ft.Text(p, size=13, color=ft.Colors.ERROR) for p in found]
        try:
            save.update()
            errors.update()
        except (RuntimeError, AssertionError):
            pass  # not on a page yet

    async def do_save(_: Any) -> None:
        if not kind.problems(current(), r):
            await on_save(current())

    save.on_click = do_save
    values = initial if initial is not None else kind.read(r)
    names = {f.name for f in fields(values)}  # type: ignore[arg-type]
    assert names == {n for _, g in kind.groups for n, _, _ in g}
    groups: list[ft.Control] = []
    for title, group in kind.groups:
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
            if show is not None and hint in (DATE, TIME):
                field.suffix_icon = _picker_button(name, hint, field, check, show)
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
                        ft.Column(
                            rows,
                            spacing=0,
                            tight=True,
                            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                        ),
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
    header = ft.Row(
        [
            ft.TextButton("Cancel", on_click=on_cancel),
            ft.Text(
                kind.title,
                size=17,
                weight=ft.FontWeight.W_700,
                expand=True,
                text_align=ft.TextAlign.CENTER,
            ),
            save,
        ],
    )
    above: list[ft.Control] = []
    if note:
        above.append(
            ft.Row(
                [
                    ft.Icon(ft.Icons.ATTACH_FILE, size=16, color=ft.Colors.ON_SURFACE_VARIANT),
                    ft.Text(note, size=13, color=ft.Colors.ON_SURFACE_VARIANT, expand=True),
                ],
                spacing=6,
            )
        )
    form = ft.Column([*above, *groups, errors], spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)
    data = {"editor": r.reference, "values": current}
    if sheet:
        return ft.BottomSheet(
            ft.Container(
                ft.Column([header, form], spacing=12),
                padding=ft.Padding.only(left=16, right=16, bottom=16),
                height=height,
            ),
            show_drag_handle=True,
            scrollable=True,
            on_dismiss=on_dismiss,
            data=data,
        )
    return ft.AlertDialog(
        modal=False,
        title=header,
        content=ft.Container(form, width=WIDTH, height=height),
        shape=ft.RoundedRectangleBorder(radius=14),
        on_dismiss=on_dismiss,
        data=data,
    )
