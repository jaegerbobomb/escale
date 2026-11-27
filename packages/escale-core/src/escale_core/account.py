"""The Nextcloud account of this device (S006b, ADR-0004).

What the preferences show and do: connect with a URL, a login and an app password,
list the calendars, choose one or create "Trips", disconnect. Nothing is saved until the
server accepts the credentials; the password goes to a ``PasswordStore``, the rest to
the settings file.
"""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urlparse

from escale_core.nextcloud import (
    TRIPS,
    Calendar,
    NextcloudError,
    NextcloudServer,
    Problem,
    connect,
    create_trips_calendar,
    endpoints,
)
from escale_core.passwords import PasswordStore
from escale_core.settings import AccountSettings, SettingsFile

ServerFor = Callable[[str, str, str], NextcloudServer]
"""Builds the adapter for a URL, a login and an app password."""


def _key(url: str, login: str) -> str:
    return f"{login}@{endpoints(url, login)[0]}"


class Account:
    def __init__(
        self, settings: SettingsFile, passwords: PasswordStore, server_for: ServerFor
    ) -> None:
        self._settings, self._passwords, self._server_for = settings, passwords, server_for
        self.saved = AccountSettings()
        self.calendars: tuple[Calendar, ...] = ()
        self.problem: Problem | None = None
        self.remembered = False
        """The password outlives the app (it is in the system keyring)."""
        self._server: NextcloudServer | None = None

    @property
    def connected(self) -> bool:
        return self._server is not None

    @property
    def host(self) -> str:
        return urlparse(endpoints(self.saved.url, self.saved.login)[0]).netloc

    @property
    def server(self) -> NextcloudServer | None:
        """The server, once the account is connected (S009b: documents need no calendar)."""
        return self._server

    def target(self) -> tuple[NextcloudServer, str] | None:
        """The server and the chosen calendar's URL, once both are known (S008a)."""
        if self._server is None or not self.saved.calendar:
            return None
        return self._server, self.saved.calendar

    @property
    def can_create_trips(self) -> bool:
        return self.connected and all(c.name != TRIPS for c in self.calendars)

    async def restore(self) -> None:
        """The account saved on this device, if its password is still in the keyring."""
        saved = self._settings.account()
        if not saved.url or not saved.login:
            return
        password = await self._passwords.get(_key(saved.url, saved.login))
        if password is not None:
            self.saved, self.remembered = saved, True
            self._server = self._server_for(saved.url, saved.login, password)

    async def connect(self, url: str, login: str, password: str) -> bool:
        server = self._server_for(url.strip(), login.strip(), password)
        found = await connect(server)
        self.problem = found.problem
        if found.problem is not None:
            return False
        self.saved = AccountSettings(url.strip(), login.strip())
        self._settings.save_account(self.saved)
        self.remembered = await self._passwords.set(
            _key(self.saved.url, self.saved.login), password
        )
        self._server, self.calendars = server, found.calendars
        return True

    async def load_calendars(self) -> None:
        if self._server is None:
            return
        try:
            self.calendars, self.problem = tuple(await self._server.calendars()), None
        except NextcloudError as e:
            self.problem = e.problem

    async def choose(self, calendar: Calendar) -> None:
        self.saved = AccountSettings(self.saved.url, self.saved.login, calendar.url)
        self._settings.save_account(self.saved)

    async def create_trips(self) -> None:
        if self._server is None:
            return
        try:
            trips = await create_trips_calendar(self._server)
        except NextcloudError as e:
            self.problem = e.problem
            return
        await self.load_calendars()
        await self.choose(trips)

    async def disconnect(self) -> None:
        """Forget the password and the account; the server is not touched."""
        if self.saved.url:
            await self._passwords.delete(_key(self.saved.url, self.saved.login))
        self._settings.save_account(None)
        self.saved, self.calendars, self.problem = AccountSettings(), (), None
        self.remembered, self._server = False, None
