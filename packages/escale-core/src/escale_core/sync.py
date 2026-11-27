"""Keeping the local store and the user's calendar in step (S008, ADR-0004).

S008a, the push half: what the calendar does not have yet (the store's outbox) is sent
as events in KDE Itinerary's format (S007), one reservation per event until batches
exist. Nothing happens without an account and a chosen calendar; an unreachable server
leaves the outbox for the next run.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from escale_core.account import Account
from escale_core.ical_mapping import new_entry, to_ics
from escale_core.nextcloud import EventChanged, NextcloudError, Problem, event_href
from escale_core.store import ReservationStore


@dataclass(frozen=True)
class SyncReport:
    sent: int = 0
    changed_elsewhere: int = 0
    """Events changed on the server since Escale last saw them; S008c resolves them."""
    problem: Problem | None = None
    """Why the run stopped early (server unreachable, credentials refused)."""


class Sync:
    def __init__(self, store: ReservationStore, account: Account) -> None:
        self._store, self._account = store, account
        self._running = asyncio.Lock()

    async def run(self) -> SyncReport:
        """Send the outbox; one run at a time."""
        async with self._running:
            return await self._push()

    async def _push(self) -> SyncReport:
        target = self._account.target()
        if target is None:
            return SyncReport()
        server, calendar = target
        sent = changed = 0
        for outgoing in await self._store.unsent():
            try:
                entry = new_entry([outgoing.reservation], uid=outgoing.uid)
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
                return SyncReport(sent, changed, e.problem)
            await self._store.sent(outgoing.reservation, entry.uid, href, etag)
            sent += 1
        return SyncReport(sent, changed)
