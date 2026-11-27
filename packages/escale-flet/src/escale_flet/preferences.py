"""Preferences (S006b), as libadwaita's AdwPreferencesDialog (ADR-0008).

One page for now, the Nextcloud account: a form (server, login, app password,
"Connect") until the server accepts it, then the account and its calendars to choose
from. Changes apply at once, there is no Save; the header holds the title and a close
button. Under 450 px it is a bottom sheet, as the stay editor.
"""

from __future__ import annotations

import contextlib
from collections.abc import Awaitable, Callable
from typing import Any

import flet as ft

from escale_core.account import Account
from escale_flet.stay_view import facts, primary

WIDTH = 560
_FIELDS = (
    ("url", "Server", "cloud.example.org"),
    ("login", "Login", ""),
    ("password", "App password", ""),
)
_HELP = (
    "Escale keeps your trips in a calendar of your Nextcloud and your tickets in its "
    "files. Create an app password in Nextcloud, under Settings › Security."  # noqa: RUF001
)


def _group(title: str, boxed: ft.Control, note: str | None = None) -> ft.Control:
    """libadwaita's AdwPreferencesGroup: a heading, a description, a boxed list."""
    head: list[ft.Control] = [
        ft.Text(title, size=13, weight=ft.FontWeight.W_700, color=ft.Colors.ON_SURFACE_VARIANT)
    ]
    if note:
        head.append(ft.Text(note, size=12.5, color=ft.Colors.ON_SURFACE_VARIANT))
    return ft.Column(
        [*head, boxed],
        spacing=6,
        tight=True,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )


def _row(label: str, on_click: Callable[[Any], Any], color: str | None = None) -> ft.Control:
    return ft.Container(
        ft.Text(label, size=14, color=color),
        padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        on_click=on_click,
        data={"action": label},
    )


class Preferences:
    """The dialog's state, kept across a rebuild when the window crosses 450 px."""

    def __init__(
        self,
        account: Account,
        on_close: Callable[[Any], Any],
        on_calendar: Callable[[], Awaitable[object]] | None = None,
    ) -> None:
        self.account = account
        self.on_close = on_close
        self.on_calendar = on_calendar
        """Run once a calendar is chosen or created: the sync (S008a)."""
        self.draft: dict[str, str] = {}
        self.busy = False
        self.body = ft.Column(spacing=22, tight=True)

    def dialog(
        self, on_dismiss: Callable[[Any], Any], sheet: bool = False, height: float = 560
    ) -> ft.AlertDialog | ft.BottomSheet:
        self.render()
        header = ft.Row(
            [
                ft.Container(width=40),
                ft.Text(
                    "Preferences",
                    size=17,
                    weight=ft.FontWeight.W_700,
                    expand=True,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.IconButton(
                    ft.Icons.CLOSE, tooltip="Close", on_click=self.on_close, data={"close": True}
                ),
            ]
        )
        page = ft.Column([self.body], scroll=ft.ScrollMode.AUTO, expand=True)
        data = {"preferences": True}
        if sheet:
            return ft.BottomSheet(
                ft.Container(
                    ft.Column([header, page], spacing=12),
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
            content=ft.Container(page, width=WIDTH, height=height),
            shape=ft.RoundedRectangleBorder(radius=14),
            on_dismiss=on_dismiss,
            data=data,
        )

    def render(self) -> None:
        self.body.controls = self._account() if self.account.connected else self._form()
        with contextlib.suppress(RuntimeError, AssertionError):  # not on a page yet
            self.body.update()

    def _act(self, work: Callable[[], Awaitable[Any]]) -> Callable[[Any], Awaitable[None]]:
        async def run(_: Any) -> None:
            if self.busy:
                return
            self.busy = True
            self.render()
            try:
                await work()
            finally:
                self.busy = False
                self.render()

        return run

    async def load(self) -> None:
        """Fetch the calendars of an account restored from the keyring."""
        await self._act(self.account.load_calendars)(None)

    # --- not connected ---

    def _form(self) -> list[ft.Control]:
        ready = all(self.draft.get(name, "").strip() for name, _, _ in _FIELDS)
        connect = primary("Connecting…" if self.busy else "Connect", self._connect)
        connect.disabled = self.busy or not ready
        entries: list[ft.Control] = []
        for name, label, hint in _FIELDS:
            field = ft.TextField(
                label=label,
                value=self.draft.get(name, ""),
                hint_text=hint or None,
                password=name == "password",
                can_reveal_password=name == "password",
                autocorrect=False,
                border=ft.NoInputBorder(),
                on_submit=self._connect,
                data={"field": name},
            )
            field.on_change = self._typed(name, field, connect)
            entries.append(
                ft.Container(field, padding=ft.Padding.symmetric(horizontal=16, vertical=2))
            )
        shown: list[ft.Control] = [_group("Nextcloud", facts(entries), _HELP)]
        if self.account.problem is not None:
            shown.append(ft.Text(self.account.problem.value, size=13, color=ft.Colors.ERROR))
        shown.append(ft.Row([connect], alignment=ft.MainAxisAlignment.CENTER))
        return shown

    def _typed(self, name: str, field: ft.TextField, connect: ft.Control) -> Callable[[Any], None]:
        def keep(_: Any) -> None:
            self.draft[name] = field.value or ""
            connect.disabled = self.busy or not all(
                self.draft.get(n, "").strip() for n, _, _ in _FIELDS
            )
            with contextlib.suppress(RuntimeError, AssertionError):
                connect.update()

        return keep

    async def _connect(self, _: Any) -> None:
        url, login, password = (self.draft.get(n, "") for n, _, _ in _FIELDS)
        if not (url.strip() and login.strip() and password) or self.busy:
            return

        async def work() -> None:
            if await self.account.connect(url, login, password):
                self.draft.clear()

        await self._act(work)(None)

    # --- connected ---

    async def _create_trips(self) -> None:
        await self.account.create_trips()
        if self.on_calendar is not None and self.account.target() is not None:
            await self.on_calendar()

    def _account(self) -> list[ft.Control]:
        a = self.account
        who = ft.Container(
            ft.Row(
                [
                    ft.Icon(ft.Icons.CLOUD_DONE_OUTLINED, size=18, color=ft.Colors.PRIMARY),
                    ft.Column(
                        [
                            ft.Text(f"Connected as {a.saved.login}", size=14),
                            ft.Text(a.host, size=12.5, color=ft.Colors.ON_SURFACE_VARIANT),
                        ],
                        spacing=2,
                        tight=True,
                        expand=True,
                    ),
                ],
                spacing=12,
            ),
            padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        )
        note = (
            None
            if a.remembered
            else (
                "No system keyring: Escale will forget the app password when it quits, and "
                "it will be asked again."
            )
        )
        account = _group(
            "Nextcloud",
            facts([who, _row("Disconnect", self._act(a.disconnect), ft.Colors.ERROR)]),
            note,
        )
        choices: list[ft.Control] = [
            ft.Container(
                ft.Radio(value=c.url, label=c.name),
                padding=ft.Padding.symmetric(horizontal=8, vertical=4),
            )
            for c in a.calendars
        ]
        if self.busy and not a.calendars:
            choices.append(
                ft.Container(
                    ft.Text("Loading the calendars…", size=14),
                    padding=ft.Padding.symmetric(horizontal=16, vertical=14),
                )
            )
        if a.can_create_trips and not self.busy:
            choices.append(_row("Create a Trips calendar", self._act(self._create_trips)))

        async def choose(e: Any) -> None:
            picked = [c for c in a.calendars if c.url == calendars.value]
            if picked:
                await a.choose(picked[0])
                if self.on_calendar is not None:
                    await self.on_calendar()

        calendars = ft.RadioGroup(
            facts(choices),
            value=a.saved.calendar or None,
            on_change=choose,
            data={"calendars": True},
        )
        shown = [
            account,
            _group("Calendar", calendars, "Escale keeps your trips in this calendar."),
        ]
        if a.problem is not None:
            shown.append(ft.Text(a.problem.value, size=13, color=ft.Colors.ERROR))
        return shown
