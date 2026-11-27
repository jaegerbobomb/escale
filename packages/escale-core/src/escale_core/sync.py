"""Keeping the local store and the user's calendar in step (S008, ADR-0004).

Each run first receives what changed on the calendar (S008b: ``sync-collection`` with the
stored token), then sends the store's outbox (S008a), as events in KDE Itinerary's
format (S007). Nothing happens without an account and a chosen calendar; an unreachable
server leaves everything for the next run.

When the same event changed both here and on the server (S008c), the server's version
wins: the local change is dropped and the run names the reservation, so that the UI
can say so. No merge, no choice, in v1 (ADR-0004).
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field

from escale_core.account import Account
from escale_core.extraction import ExtractedReservation
from escale_core.ical_mapping import entries_in, new_entry, to_ics
from escale_core.nextcloud import (
    EventChanged,
    NextcloudError,
    NextcloudServer,
    Problem,
    RemoteEvent,
    event_href,
)
from escale_core.store import ReservationStore


@dataclass(frozen=True)
class SyncReport:
    sent: int = 0
    received: int = 0
    """Events added, changed or removed locally because the calendar changed."""
    changed_elsewhere: tuple[ExtractedReservation, ...] = ()
    """Reservations whose local change gave way to the server's version (S008c)."""
    problem: Problem | None = None
    """Why the run stopped early (server unreachable, credentials refused)."""


@dataclass
class _Run:
    received: int = 0
    sent: int = 0
    changed_elsewhere: list[ExtractedReservation] = field(default_factory=list)
    settled: set[str] = field(default_factory=set)
    """Hrefs whose conflict this run already resolved: not sent again."""

    def report(self, problem: Problem | None = None) -> SyncReport:
        return SyncReport(self.sent, self.received, tuple(self.changed_elsewhere), problem)


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
            run = _Run()
            try:
                await self._pull(server, calendar, run)
                await self._push(server, calendar, run)
            except NextcloudError as e:
                return run.report(e.problem)
            return run.report()

    async def _apply(self, event: RemoteEvent, run: _Run, force: bool = False) -> None:
        """The calendar's version of ``event``. A local change waiting to be sent is
        dropped for it (S008c), and the reservation named in the report."""
        for entry in entries_in(event.ics):
            kept = await self._store.received(
                entry.uid, event.href, event.etag, entry.reservations, force
            )
            if not kept:
                await self._store.received(
                    entry.uid, event.href, event.etag, entry.reservations, True
                )
            run.received += 1
            if force or not kept:
                run.changed_elsewhere.append(entry.reservations[0])
                run.settled.add(event.href)

    async def _gone(self, href: str, run: _Run, local: Sequence[ExtractedReservation]) -> None:
        """The event at ``href`` was deleted elsewhere; a local change of it gives way."""
        if not await self._store.removed(href):
            await self._store.removed(href, force=True)
            run.settled.add(href)
            if local:
                run.changed_elsewhere.append(local[0])
        run.received += 1

    async def _pull(self, server: NextcloudServer, calendar: str, run: _Run) -> None:
        pending = {o.href: o.batch for o in await self._store.unsent() if o.href}
        token = await self._store.calendar_token(calendar)
        changes = await server.changes(calendar, token)
        known = await self._store.events()
        for event in changes.changed:
            if known.get(event.href) != event.etag:  # else: what this device sent
                await self._apply(event, run)
        gone = list(changes.removed)
        if changes.full:
            listed = {e.href for e in changes.changed}
            gone += [href for href in known if href not in listed]
        for href in gone:
            if href in known:
                await self._gone(href, run, pending.get(href, ()))
        await self._store.set_calendar_token(calendar, changes.token)

    async def _push(self, server: NextcloudServer, calendar: str, run: _Run) -> None:
        for outgoing in await self._store.unsent():
            if outgoing.href in run.settled:
                continue
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
                # changed on the server after the pull: its version wins (S008c)
                current = await server.get_event(href)
                if current is None:
                    await self._gone(href, run, batch)
                else:
                    await self._apply(current, run, force=True)
                continue
            await self._store.sent(batch, entry.uid, href, etag)
            run.sent += 1
