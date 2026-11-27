"""The Nextcloud adapter: CalDAV and WebDAV through the ``caldav`` library (S006a).

``caldav``'s client is synchronous; each call runs in a worker thread. Its errors are
turned into ``NextcloudError``s the service understands.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import TypeVar

from caldav.davclient import DAVClient
from caldav.lib import error as dav_error
from niquests import exceptions as http_error

from escale_core.nextcloud import (
    Calendar,
    CredentialsRefused,
    EventChanged,
    NextcloudError,
    NotNextcloud,
    ServerUnreachable,
    endpoints,
)

T = TypeVar("T")
TIMEOUT_S = 20


class NextcloudDav:
    """One account on one server: ``url`` as the user typed it, a login, an app password."""

    def __init__(self, url: str, login: str, password: str) -> None:
        self._dav, self._files = endpoints(url, login)
        self._client = DAVClient(
            url=self._dav, username=login, password=password, timeout=TIMEOUT_S
        )

    async def _run(self, work: Callable[[], T]) -> T:
        try:
            return await asyncio.to_thread(work)
        except dav_error.AuthorizationError as e:
            raise CredentialsRefused from e
        except (http_error.ConnectionError, http_error.Timeout, OSError) as e:
            raise ServerUnreachable from e
        except dav_error.DAVError as e:
            raise NotNextcloud from e
        except NextcloudError:
            raise

    async def calendars(self) -> list[Calendar]:
        def work() -> list[Calendar]:
            return [
                Calendar(c.get_display_name() or str(c.url), str(c.url))
                for c in self._client.principal().calendars()  # type: ignore[no-untyped-call]
            ]

        return await self._run(work)

    async def create_calendar(self, name: str) -> Calendar:
        def work() -> Calendar:
            created = self._client.principal().make_calendar(name=name)  # type: ignore[no-untyped-call]
            return Calendar(name, str(created.url))

        return await self._run(work)

    async def folder_exists(self, name: str) -> bool:
        def work() -> bool:
            response = self._client.propfind(self._folder(name), depth=0)
            if response.status == 401:
                raise dav_error.AuthorizationError(self._files)
            return bool(response.status == 207)

        return await self._run(work)

    async def create_folder(self, name: str) -> None:
        def work() -> None:
            self._client.mkcol(self._folder(name), "")

        await self._run(work)

    async def put_event(self, href: str, ics: bytes, etag: str | None) -> str | None:
        headers = {"Content-Type": "text/calendar; charset=utf-8"}
        headers.update({"If-Match": etag} if etag else {"If-None-Match": "*"})

        def work() -> str | None:
            response = self._client.put(href, ics.decode(), headers)
            if response.status == 412:
                raise EventChanged
            if response.status == 401:
                raise dav_error.AuthorizationError(href)
            if response.status >= 400:
                raise dav_error.PutError(f"{response.status} {response.reason}")
            tag = response.headers.get("ETag")
            return str(tag) if tag else None

        return await self._run(work)

    def _folder(self, name: str) -> str:
        return f"{self._files}{name}/"
