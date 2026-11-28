"""Adwaita-like look for Flet (SPEC.md § Look, ADR-0001).

Colours follow libadwaita's named colours and the GNOME palette; they are tokens, so
components ask for ``tokens(brightness).warning`` instead of hard-coding a colour.
"""

from __future__ import annotations

from dataclasses import dataclass

import flet as ft

FONT_FAMILY = "Adwaita Sans"
FONT_FAMILY_BOLD = "Adwaita Sans Bold"

#: Font files shipped in ``assets/fonts`` (latin subset, SIL OFL 1.1). Flet maps one
#: file per family, so the bold weight is a family of its own.
FONTS = {
    FONT_FAMILY: "fonts/AdwaitaSans-Regular.ttf",
    FONT_FAMILY_BOLD: "fonts/AdwaitaSans-Bold.ttf",
}


@dataclass(frozen=True)
class Tokens:
    """Colours of one variant (light or dark) of the theme."""

    accent: str
    """Interactive elements; also the "planned" state (added from a search, not booked)."""
    accent_bg: str
    on_accent_bg: str
    success: str
    """On time, confirmed."""
    warning: str
    """Delayed, tight connection."""
    error: str
    """Cancelled."""
    outing: str
    """Outings (purple)."""
    window_bg: str
    view_bg: str
    headerbar_bg: str
    card_bg: str
    fg: str
    dim_fg: str
    border: str


LIGHT = Tokens(
    accent="#1c71d8",
    accent_bg="#3584e4",
    on_accent_bg="#ffffff",
    success="#1b8553",
    warning="#9c6e03",
    error="#c01c28",
    outing="#9141ac",
    window_bg="#fafafb",
    view_bg="#ffffff",
    headerbar_bg="#ffffff",
    card_bg="#ffffff",
    fg="#323233",
    dim_fg="#6e6e73",
    border="#e0e0e3",
)

DARK = Tokens(
    accent="#78aeed",
    accent_bg="#3584e4",
    on_accent_bg="#ffffff",
    success="#78e9ab",
    warning="#ffc252",
    error="#ff938c",
    outing="#dc8add",
    window_bg="#222226",
    view_bg="#1d1d20",
    headerbar_bg="#2e2e32",
    card_bg="#36363a",
    fg="#ffffff",
    dim_fg="#b0b0b4",
    border="#3d3d42",
)


def tokens(brightness: ft.Brightness) -> Tokens:
    """Tokens of the variant matching ``brightness``."""
    return DARK if brightness == ft.Brightness.DARK else LIGHT


def _text_theme(t: Tokens) -> ft.TextTheme:
    bold = ft.TextStyle(font_family=FONT_FAMILY_BOLD, color=t.fg)
    return ft.TextTheme(
        title_large=bold,
        title_medium=bold,
        title_small=bold,
        label_large=ft.TextStyle(font_family=FONT_FAMILY_BOLD),
        headline_small=bold,
    )


def build_theme(t: Tokens) -> ft.Theme:
    """A Flet theme for one variant."""
    return ft.Theme(
        font_family=FONT_FAMILY,
        use_material3=True,
        color_scheme=ft.ColorScheme(
            primary=t.accent_bg,
            on_primary=t.on_accent_bg,
            secondary=t.accent,
            tertiary=t.success,
            on_tertiary=t.on_accent_bg,
            error=t.error,
            surface=t.window_bg,
            on_surface=t.fg,
            on_surface_variant=t.dim_fg,
            outline=t.border,
            outline_variant=t.border,
            surface_container=t.card_bg,
            tertiary_container=t.outing,
        ),
        scaffold_bgcolor=t.window_bg,
        appbar_theme=ft.AppBarTheme(
            bgcolor=t.headerbar_bg,
            color=t.fg,
            elevation=0,
            elevation_on_scroll=0,
        ),
        navigation_bar_theme=ft.NavigationBarTheme(
            bgcolor=t.headerbar_bg,
            indicator_color=ft.Colors.with_opacity(0.15, t.fg),
            elevation=0,
        ),
        text_theme=_text_theme(t),
    )


OUTING = ft.Colors.TERTIARY_CONTAINER
"""Outings' purple, light or dark with the theme (S035); no Material widget of Escale
uses the tertiary container otherwise."""

LIGHT_THEME = build_theme(LIGHT)
DARK_THEME = build_theme(DARK)
