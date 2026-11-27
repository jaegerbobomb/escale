"""Connecting to the user's Nextcloud (S006a, ADR-0004).

The calendar holds the reservations (CalDAV), the files hold the documents (WebDAV,
under ``Escale/``). This module checks an account and prepares it; the adapters that
talk to a server are in ``escale_core.adapters`` (``nextcloud_dav``, and a fake).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol
from urllib.parse import quote

TRIPS = "Trips"
"""The calendar Escale creates when the user has none to give it."""
FOLDER = "Escale"
"""The folder of the user's files that holds the documents (SPEC § Documents)."""


@dataclass(frozen=True)
class Calendar:
    name: str
    url: str


class Problem(Enum):
    """Why a connection failed, in words the UI can say."""

    REFUSED = "The server refused the login or the app password."
    UNREACHABLE = "The server cannot be reached."
    NOT_NEXTCLOUD = "No Nextcloud answers at this address."
    CHANGED = "The event was changed on the server meanwhile."
    BUSY = "The server asks to try again later."


class NextcloudError(Exception):
    problem: Problem


class CredentialsRefused(NextcloudError):
    problem = Problem.REFUSED


class ServerUnreachable(NextcloudError):
    problem = Problem.UNREACHABLE


class NotNextcloud(NextcloudError):
    problem = Problem.NOT_NEXTCLOUD


class ServerBusy(NextcloudError):
    """``429``: the server limits how often it is asked (S008b)."""

    problem = Problem.BUSY


class EventChanged(NextcloudError):
    """``412``: the event is not in the state Escale last saw (S008a, S008c)."""

    problem = Problem.CHANGED


class NextcloudServer(Protocol):
    """What Escale needs from a Nextcloud; adapters raise ``NextcloudError``."""

    async def calendars(self) -> list[Calendar]: ...

    async def create_calendar(self, name: str) -> Calendar: ...

    async def folder_exists(self, name: str) -> bool: ...

    async def create_folder(self, name: str) -> None: ...

    async def put_event(self, href: str, ics: bytes, etag: str | None) -> str | None:
        """Write a calendar object: a new one when ``etag`` is ``None``, else the one
        with that ETag; ``EventChanged`` otherwise. Returns its new ETag, if given."""
        ...

    async def changes(self, calendar: str, token: str | None) -> Changes:
        """What changed in ``calendar`` since ``token`` (RFC 6578 ``sync-collection``);
        everything, as a full listing, when there is no token or the server refused it."""
        ...


@dataclass(frozen=True)
class RemoteEvent:
    href: str
    """Absolute URL of the calendar object."""
    etag: str | None
    ics: bytes


@dataclass(frozen=True)
class Changes:
    token: str | None
    changed: tuple[RemoteEvent, ...] = ()
    removed: tuple[str, ...] = ()
    full: bool = False
    """``changed`` lists every event of the calendar: one not listed is gone."""


@dataclass(frozen=True)
class Connection:
    calendars: tuple[Calendar, ...]
    problem: Problem | None = None


def event_href(calendar: str, uid: str) -> str:
    """Where Escale puts a new event: ``<calendar>/<uid>.ics``."""
    return f"{calendar.rstrip('/')}/{quote(uid, safe='')}.ics"


def endpoints(url: str, login: str) -> tuple[str, str]:
    """The DAV root and the user's files root, from what the user typed as the server."""
    base = url.strip().rstrip("/")
    if "://" not in base:
        base = "https://" + base
    base = base.removesuffix("/index.php").rstrip("/")
    dav = base + "/remote.php/dav"
    return dav, f"{dav}/files/{quote(login, safe='')}/"


async def connect(server: NextcloudServer) -> Connection:
    """Check the account, list its calendars, make sure the ``Escale`` folder exists."""
    try:
        calendars = await server.calendars()
        if not await server.folder_exists(FOLDER):
            await server.create_folder(FOLDER)
    except NextcloudError as e:
        return Connection((), e.problem)
    return Connection(tuple(calendars))


async def create_trips_calendar(server: NextcloudServer) -> Calendar:
    """The "Trips" calendar, created unless it is already there."""
    for calendar in await server.calendars():
        if calendar.name == TRIPS:
            return calendar
    return await server.create_calendar(TRIPS)
