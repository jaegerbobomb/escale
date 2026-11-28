"""Action dialogs that edit a booking (S017b, S029a), as GNOME action dialogs (S061,
ADR-0008).

The fields of KDE Itinerary's editor for that kind of booking, as entry rows in boxed
lists, one list per section. The header holds "Cancel", the heading and "Save"
(suggested), insensitive with the reasons below the form while the fields are not
valid. Return saves, Esc cancels. Under 450 px it is a bottom sheet, closed by Cancel or
by swiping it down, as libadwaita's AdwDialog in its automatic presentation mode.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass, fields, replace
from typing import Any

import flet as ft

from escale_core.extraction import ExtractedReservation

Groups = Sequence[tuple[str, Sequence[tuple[str, str, str]]]]
"""Sections: title, then (field, label, hint) rows."""
WIDTH = 560


@dataclass(frozen=True)
class EditorKind[F]:
    """What an editor edits: its heading, its sections, and the core's functions."""

    title: str
    groups: Groups
    read: Callable[[ExtractedReservation], F]
    problems: Callable[[F, ExtractedReservation], list[str]]


def _entry_row(field: ft.TextField) -> ft.Control:
    return ft.Container(field, padding=ft.Padding.symmetric(horizontal=16, vertical=2))


def action_editor[F](
    kind: EditorKind[F],
    r: ExtractedReservation,
    on_save: Callable[[F], Awaitable[None]],
    on_cancel: Callable[[Any], Any],
    on_dismiss: Callable[[Any], Any],
    sheet: bool = False,
    height: float = 640,
    initial: F | None = None,
) -> ft.AlertDialog | ft.BottomSheet:
    """A floating dialog, or a bottom sheet on a phone (``sheet``), as libadwaita's
    AdwDialog presents itself. ``data["values"]`` gives the fields as typed so far."""
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
    form = ft.Column([*groups, errors], spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)
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
