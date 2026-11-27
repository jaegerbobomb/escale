"""Keeping the local store and the user's calendar in step (S008, ADR-0004).

Each run first receives what changed on the calendar (S008b: ``sync-collection`` with the
stored token), then sends the store's outbox (S008a), as events in KDE Itinerary's
format (S007). Nothing happens without an account and a chosen calendar; an unreachable
server leaves everything for the next run. A local change waiting to be sent is never
overwritten by the calendar's version: S008c decides between the two.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from escale_core.account import Account
from escale_core.ical_mapping import entries_in, new_entry, to_ics
from escale_core.nextcloud import (
    EventChanged,
    NextcloudError,
    NextcloudServer,
    Problem,
    event_href,
)
from escale_core.store import ReservationStore


@dataclass(frozen=True)
class SyncReport:
    sent: int = 0
    received: int = 0
    """Events added, changed or removed locally because the calendar changed."""
    changed_elsewhere: int = 0
    """Events changed on the server while a local change waits; S008c resolves them."""
    problem: Problem | None = None
    """Why the run stopped early (server unreachable, credentials refused)."""


class Sync:
    def __init__(self, store: ReservationStore, account: Account) -> None:
        self._store, self._account = store, account
        self._running = asyncio.Lock()

    async def run(self) -> SyncReport:
        """Receive, then send; one run at a time."""
        async with self._running:
            target = self._account.target()
            if target is None:
                return SyncReport()
            server, calendar = target
            try:
                received, conflicts = await self._pull(server, calendar)
            except NextcloudError as e:
                return SyncReport(problem=e.problem)
            return await self._push(server, calendar, received, conflicts)

    async def _pull(self, server: NextcloudServer, calendar: str) -> tuple[int, set[str]]:
        """Apply the calendar's changes; returns how many, and the hrefs left in conflict."""
        token = await self._store.calendar_token(calendar)
        changes = await server.changes(calendar, token)
        known = await self._store.events()
        received = 0
        conflicts: set[str] = set()
        for event in changes.changed:
            if known.get(event.href) == event.etag:
                continue  # what this device sent itself
            entries = entries_in(event.ics)
            if not entries:
                continue  # a plain event, not a reservation
            for entry in entries:
                if await self._store.received(
                    entry.uid, event.href, event.etag, entry.reservations
                ):
                    received += 1
                else:
                    conflicts.add(event.href)
        gone = list(changes.removed)
        if changes.full:
            listed = {e.href for e in changes.changed}
            gone += [href for href in known if href not in listed]
        for href in gone:
            if href not in known:
                continue
            if await self._store.removed(href):
                received += 1
            else:
                conflicts.add(href)
        await self._store.set_calendar_token(calendar, changes.token)
        return received, conflicts

    async def _push(
        self, server: NextcloudServer, calendar: str, received: int, conflicts: set[str]
    ) -> SyncReport:
        sent, changed = 0, len(conflicts)
        for outgoing in await self._store.unsent():
            if outgoing.href in conflicts:
                continue  # the server has a newer version: S008c decides
            batch = outgoing.batch or (outgoing.reservation,)
            try:
                entry = new_entry(list(batch), uid=outgoing.uid)
                ics = to_ics([entry])
            except ValueError:
                continue  # no date: no calendar event
            href = outgoing.href or event_href(calendar, entry.uid)
            try:
                etag = await server.put_event(href, ics, outgoing.etag)
            except EventChanged:
                changed += 1
                continue
            except NextcloudError as e:
                return SyncReport(sent, received, changed, e.problem)
            await self._store.sent(batch, entry.uid, href, etag)
            sent += 1
        return SyncReport(sent, received, changed)
