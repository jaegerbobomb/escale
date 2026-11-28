"""Choosing what to add by hand (S018): "Add → Add manually…", and "Add manually" on an
import that found nothing.

An action dialog (ADR-0008) listing the kinds of booking as activatable rows in a boxed
list; a kind whose editor does not exist yet is insensitive. Under 450 px it is a bottom
sheet, as the editors are.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import flet as ft

from escale_flet.editor import WIDTH

KINDS: tuple[tuple[str, str, ft.IconData, bool], ...] = (
    ("stay", "Stay", ft.Icons.HOTEL_OUTLINED, True),
    ("flight", "Flight", ft.Icons.FLIGHT_OUTLINED, False),  # S029b
    ("train", "Train", ft.Icons.TRAIN_OUTLINED, False),
    ("bus", "Bus", ft.Icons.DIRECTIONS_BUS_OUTLINED, True),  # S030
    ("ferry", "Ferry", ft.Icons.DIRECTIONS_BOAT_OUTLINED, True),  # S030
    ("event", "Event", ft.Icons.LOCAL_ACTIVITY_OUTLINED, False),
    ("restaurant", "Restaurant", ft.Icons.RESTAURANT_OUTLINED, False),
)
"""Key, label, icon, and whether its editor exists."""
TITLE = "Add Manually"


def _row(key: str, label: str, icon: ft.IconData, enabled: bool, on_pick: Any) -> ft.Control:
    dim = None if enabled else ft.Colors.with_opacity(0.38, ft.Colors.ON_SURFACE)
    return ft.ListTile(
        leading=ft.Icon(icon),
        title=ft.Text(label),
        trailing=ft.Icon(ft.Icons.CHEVRON_RIGHT, color=dim),  # insensitive as the row
        disabled=not enabled,
        on_click=(lambda _: on_pick(key)) if enabled else None,
        data={"manual_kind": key},
    )


def kind_chooser(
    on_pick: Callable[[str], Any],
    on_cancel: Callable[[Any], Any],
    sheet: bool = False,
) -> ft.AlertDialog | ft.BottomSheet:
    """The kinds of booking to add; ``on_pick`` gets the chosen kind's key."""
    rows: list[ft.Control] = []
    for key, label, icon, enabled in KINDS:
        if rows:
            rows.append(ft.Divider(height=1, thickness=1, color=ft.Colors.OUTLINE_VARIANT))
        rows.append(_row(key, label, icon, enabled, on_pick))
    boxed = ft.Container(
        ft.Column(rows, spacing=0, tight=True),
        bgcolor=ft.Colors.SURFACE_CONTAINER,
        border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
        border_radius=12,
    )
    header = ft.Row(
        [
            ft.TextButton("Cancel", on_click=on_cancel),
            ft.Text(
                TITLE,
                size=17,
                weight=ft.FontWeight.W_700,
                expand=True,
                text_align=ft.TextAlign.CENTER,
            ),
            ft.Container(width=64),  # balances "Cancel": the heading stays centred
        ]
    )
    if sheet:
        return ft.BottomSheet(
            ft.Container(
                ft.Column([header, boxed], spacing=12, tight=True, scroll=ft.ScrollMode.AUTO),
                padding=ft.Padding.only(left=16, right=16, bottom=16),
            ),
            show_drag_handle=True,
            data={"manual_kinds": True},
        )
    return ft.AlertDialog(
        modal=False,
        title=header,
        content=ft.Container(boxed, width=WIDTH),
        shape=ft.RoundedRectangleBorder(radius=14),
        data={"manual_kinds": True},
    )
