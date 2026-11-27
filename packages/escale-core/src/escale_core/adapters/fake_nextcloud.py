"""A Nextcloud in memory, for the service and UI tests (S006a)."""

from __future__ import annotations

from dataclasses import dataclass, field

from escale_core.nextcloud import (
    Calendar,
    CredentialsRefused,
    EventChanged,
    NotNextcloud,
    ServerUnreachable,
)


@dataclass
class FakeNextcloud:
    calendars_named: list[str] = field(default_factory=list)
    folders: set[str] = field(default_factory=set)
    password_ok: bool = True
    reachable: bool = True
    nextcloud: bool = True

    def __init__(
        self,
        calendars: list[str] | None = None,
        folders: set[str] | None = None,
        password_ok: bool = True,
        reachable: bool = True,
        nextcloud: bool = True,
    ) -> None:
        self.calendars_named = list(calendars or [])
        self.folders = set(folders or ())
        self.password_ok, self.reachable, self.nextcloud = password_ok, reachable, nextcloud
        self.events: dict[str, dict[str, tuple[bytes, str]]] = {}
        """Calendar URL -> event name (its uid) -> (ICS, ETag)."""
        self._version = 0

    def _check(self) -> None:
        if not self.reachable:
            raise ServerUnreachable
        if not self.nextcloud:
            raise NotNextcloud
        if not self.password_ok:
            raise CredentialsRefused

    @staticmethod
    def calendar_url(name: str) -> str:
        return f"https://cloud.test/remote.php/dav/calendars/u/{name.lower()}/"

    @classmethod
    def _calendar(cls, name: str) -> Calendar:
        return Calendar(name, cls.calendar_url(name))

    async def calendars(self) -> list[Calendar]:
        self._check()
        return [self._calendar(n) for n in self.calendars_named]

    async def create_calendar(self, name: str) -> Calendar:
        self._check()
        self.calendars_named.append(name)
        return self._calendar(name)

    async def folder_exists(self, name: str) -> bool:
        self._check()
        return name in self.folders

    async def create_folder(self, name: str) -> None:
        self._check()
        self.folders.add(name)

    def _etag(self) -> str:
        self._version += 1
        return f'"{self._version}"'

    async def put_event(self, href: str, ics: bytes, etag: str | None) -> str | None:
        self._check()
        calendar, _, name = href.rpartition("/")
        events = self.events.setdefault(calendar + "/", {})
        uid = name.removesuffix(".ics")
        current = events.get(uid)
        if (etag is None) != (current is None) or (current and current[1] != etag):
            raise EventChanged
        events[uid] = (ics, self._etag())
        return events[uid][1]

    def touch_all(self) -> None:
        """Every event changed by someone else: new ETags."""
        for events in self.events.values():
            for uid, (ics, _) in events.items():
                events[uid] = (ics, self._etag())
