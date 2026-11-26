"""Test helpers: a stand-in for `ft.Page`, which needs a connected Flutter client."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any, cast

import flet as ft


@dataclass
class FakePage:
    """The part of `ft.Page` the app uses, with the same attributes and events."""

    width: float | None = None
    route: str = "/"
    platform: ft.PagePlatform = ft.PagePlatform.LINUX
    web: bool = False
    platform_brightness: ft.Brightness = ft.Brightness.LIGHT
    title: str | None = None
    fonts: dict[str, str] | None = None
    theme: ft.Theme | None = None
    dark_theme: ft.Theme | None = None
    theme_mode: ft.ThemeMode | None = None
    padding: Any = None
    appbar: ft.AppBar | None = None
    navigation_bar: ft.NavigationBar | None = None
    on_resize: Any = None
    controls: list[ft.Control] = field(default_factory=list)
    dialogs: list[ft.DialogControl] = field(default_factory=list)
    updates: int = 0

    def add(self, *controls: ft.Control) -> None:
        self.controls.extend(controls)

    def update(self) -> None:
        self.updates += 1

    def show_dialog(self, dialog: ft.DialogControl) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> ft.DialogControl | None:
        return self.dialogs.pop() if self.dialogs else None

    @property
    def dialog(self) -> ft.DialogControl | None:
        """The dialog or sheet on top, if any."""
        return self.dialogs[-1] if self.dialogs else None

    def resize(self, width: float) -> None:
        self.width = width
        event = ft.PageResizeEvent(
            name="resize", control=cast(ft.Page, self), width=width, height=800
        )
        self.on_resize(event)

    def effective_theme(self) -> ft.Theme | None:
        """The theme Flutter applies for this page's mode and platform brightness."""
        dark = self.theme_mode == ft.ThemeMode.DARK or (
            self.theme_mode == ft.ThemeMode.SYSTEM
            and self.platform_brightness == ft.Brightness.DARK
        )
        return self.dark_theme if dark else self.theme


def walk(control: Any) -> Iterator[Any]:
    """Every control under ``control``, itself included."""
    if control is None:
        return
    if isinstance(control, list):
        for item in control:
            yield from walk(item)
        return
    yield control
    for name in ("content", "controls", "actions", "title"):
        child = getattr(control, name, None)
        if isinstance(child, list):
            for item in child:
                yield from walk(item)
        elif child is not None and not isinstance(child, str):
            yield from walk(child)


def texts(control: Any) -> list[str]:
    """The text of every `ft.Text` and button label under ``control``."""
    found: list[str] = []
    for c in walk(control):
        if isinstance(c, ft.Text) and c.value:
            found.append(c.value)
        elif isinstance(
            c, ft.Button | ft.FilledButton | ft.OutlinedButton | ft.TextButton
        ) and isinstance(c.content, str):
            found.append(c.content)
    return found


def button(control: Any, label: str) -> Any:
    """The button labelled ``label`` under ``control``."""
    for c in walk(control):
        if (
            isinstance(c, ft.Button | ft.FilledButton | ft.OutlinedButton | ft.TextButton)
            and c.content == label
        ):
            return c
    raise LookupError(f"no button {label!r}")


def tagged(control: Any, key: str, value: Any = True) -> Any:
    """The one control under ``control`` whose ``data[key]`` is ``value``."""
    found = [c for c in walk(control) if isinstance(c.data, dict) and c.data.get(key) == value]
    if len(found) != 1:
        raise LookupError(f"{len(found)} controls with {key}={value!r}")
    return found[0]


def action(control: Any, label: str) -> Any:
    """The action row labelled ``label`` (ADR-0008: secondary actions are rows)."""
    return tagged(control, "action", label)


def click(control: Any) -> None:
    """Run a control's ``on_click`` handler, sync or async, as Flet would."""
    handler = control.on_click
    outcome = handler(None)
    if inspect.iscoroutine(outcome):
        asyncio.run(outcome)
