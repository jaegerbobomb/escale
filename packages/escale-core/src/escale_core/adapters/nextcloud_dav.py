"""The Nextcloud adapter: CalDAV and WebDAV through the ``caldav`` library (S006a).

``caldav``'s client is synchronous; each call runs in a worker thread. Its errors are
turned into ``NextcloudError``s the service understands.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from typing import Any, TypeVar
from urllib.parse import quote, urljoin
from xml.sax.saxutils import escape

from caldav.davclient import DAVClient
from caldav.lib import error as dav_error
from caldav.lib.python_utilities import WireBytes
from niquests import exceptions as http_error

from escale_core.nextcloud import (
    Calendar,
    Changes,
    CredentialsRefused,
    EventChanged,
    NextcloudError,
    NotNextcloud,
    RemoteEvent,
    ServerBusy,
    ServerUnreachable,
    endpoints,
)

T = TypeVar("T")
_SYNC_COLLECTION = """<?xml version="1.0" encoding="utf-8"?>
<d:sync-collection xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav">
  <d:sync-token>{token}</d:sync-token>
  <d:sync-level>1</d:sync-level>
  <d:prop><d:getetag/><c:calendar-data/></d:prop>
</d:sync-collection>"""
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
        except dav_error.RateLimitError as e:
            raise ServerBusy from e
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

    async def file_exists(self, path: str) -> bool:
        def work() -> bool:
            response = self._client.propfind(self._file(path), depth=0)
            if response.status == 401:
                raise dav_error.AuthorizationError(self._files)
            return bool(response.status == 207)

        return await self._run(work)

    async def put_file(self, path: str, content: bytes, content_type: str) -> bool:
        headers = {"Content-Type": content_type, "If-None-Match": "*"}
        # sent as is: caldav turns the line ends of a plain body into CRLF
        body: Any = WireBytes(content)

        def put() -> int:
            return int(self._client.put(self._file(path), body, headers).status)

        def work() -> bool:
            status = put()
            if status == 404:  # Nextcloud: a folder on the way is missing
                parts = path.split("/")[:-1]
                for n in range(1, len(parts) + 1):
                    made = self._client.mkcol(self._file("/".join(parts[:n])) + "/", "")
                    if made.status not in (201, 405):  # 405: already there
                        raise dav_error.MkcolError(f"{made.status} {made.reason}")
                status = put()
            if status == 412:  # already there: a document never changes
                return False
            if status >= 400:
                raise dav_error.PutError(f"{status}")
            return True

        return await self._run(work)

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

    async def get_event(self, href: str) -> RemoteEvent | None:
        def work() -> RemoteEvent | None:
            response = self._client.request(href)
            if response.status == 404:
                return None
            if response.status >= 400:
                raise dav_error.NotFoundError(f"{response.status} {response.reason}")
            tag = response.headers.get("ETag")
            body = response.raw
            return RemoteEvent(
                href,
                str(tag) if tag else None,
                body if isinstance(body, bytes) else str(body).encode(),
            )

        return await self._run(work)

    async def changes(self, calendar: str, token: str | None) -> Changes:
        def report(token: str | None) -> Any:
            body = _SYNC_COLLECTION.format(token=escape(token or ""))
            return self._client.request(
                calendar, "REPORT", body, {"Depth": "0", "Content-Type": "application/xml"}
            )

        def work() -> Changes:
            # A refused token (Nextcloud: 403, which caldav raises as an authorisation
            # error) means starting over with a full listing; refused credentials fail
            # that one too.
            try:
                response, full = report(token), token is None
            except dav_error.AuthorizationError:
                if token is None:
                    raise
                response, full = report(None), True
            if response.status in (400, 403, 409, 412) and token is not None:
                response, full = report(None), True
            if response.status == 401:
                raise dav_error.AuthorizationError(calendar)
            result = response.parse_sync_collection()
            changed = tuple(
                RemoteEvent(urljoin(calendar, c.href), c.etag, c.calendar_data.encode())
                for c in result.changed
                if c.calendar_data
            )
            removed = tuple(urljoin(calendar, href) for href in result.deleted)
            return Changes(result.sync_token, changed, removed, full)

        return await self._run(work)

    def _file(self, path: str) -> str:
        return self._files + quote(path)

    def _folder(self, name: str) -> str:
        return f"{self._files}{name}/"
