"""A Nextcloud in memory, for the service and UI tests (S006a)."""

from __future__ import annotations

from dataclasses import dataclass, field

from escale_core.nextcloud import (
    Calendar,
    Changes,
    CredentialsRefused,
    EventChanged,
    NotNextcloud,
    RemoteEvent,
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
        self._log: list[tuple[int, str, str]] = []
        """(version, calendar, name) of each write or delete, for ``changes``."""
        self._epoch = 0
        self.files: dict[str, bytes] = {}
        """Path relative to the user's files -> content (S009a)."""
        self.written: list[str] = []
        """The files written, in order."""
        self.uploads = 0

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

    async def file_exists(self, path: str) -> bool:
        self._check()
        return path in self.files

    async def put_file(self, path: str, content: bytes, content_type: str) -> bool:
        self._check()
        if path in self.files:
            return False
        parts = path.split("/")
        self.folders.update("/".join(parts[:n]) for n in range(1, len(parts)))
        self.files[path] = content
        self.written.append(path)
        self.uploads += 1
        return True

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
        self._log.append((self._version, calendar + "/", uid))
        return events[uid][1]

    def touch_all(self) -> None:
        """Every event changed by someone else: new ETags."""
        for calendar, events in self.events.items():
            for uid, (ics, _) in events.items():
                events[uid] = (ics, self._etag())
                self._log.append((self._version, calendar, uid))

    def delete_all(self) -> None:
        """Every event deleted by someone else."""
        for calendar, events in self.events.items():
            for uid in list(events):
                del events[uid]
                self._version += 1
                self._log.append((self._version, calendar, uid))

    def forget_tokens(self) -> None:
        """The server lost its sync history: earlier tokens are refused."""
        self._epoch += 1

    async def get_event(self, href: str) -> RemoteEvent | None:
        self._check()
        calendar, _, name = href.rpartition("/")
        found = self.events.get(calendar + "/", {}).get(name.removesuffix(".ics"))
        return RemoteEvent(href, found[1], found[0]) if found else None

    async def changes(self, calendar: str, token: str | None) -> Changes:
        self._check()
        events = self.events.get(calendar, {})
        now = f"{self._epoch}:{self._version}"
        epoch, _, since = (token or "").partition(":")
        if token is None or epoch != str(self._epoch):
            listed = tuple(RemoteEvent(calendar + n + ".ics", e, i) for n, (i, e) in events.items())
            return Changes(now, listed, full=True)
        names = {n for v, c, n in self._log if c == calendar and v > int(since)}
        changed = tuple(
            RemoteEvent(calendar + n + ".ics", events[n][1], events[n][0])
            for n in sorted(names)
            if n in events
        )
        removed = tuple(calendar + n + ".ics" for n in sorted(names) if n not in events)
        return Changes(now, changed, removed)
