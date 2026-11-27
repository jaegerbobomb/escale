---
id: S008b
title: "Receive changes from the calendar"
epic: sync
depends_on: [S008a]
status: done
estimate: M
bdd: true
updated: "2026-11-27"
adr: [4]
released_in: "0.21.0"
---

## User story

> **As a** traveller with a laptop and a phone, **I want** what was added, changed or
> deleted on one to show on the other, **so that** I never wonder which device is right.

## Technical description

- Child of S008. Core service `sync`, pull half: a `sync-collection` REPORT (RFC 6578)
  with the stored sync-token; added and changed events are read with S007 and written
  to the local store by `UID`, removed ones are deleted from it; the new token is kept.
- Fallback when the server refuses sync-tokens: list the calendar's ETags and fetch the
  events whose ETag changed.
- Events written by KDE Itinerary are taken in too (S007 reads them); plain events are
  ignored.
- Runs before each push (S008a): at start, after a local change, and every 10 minutes
  while the app is open. "Current" is refreshed when something changed.
- A reservation with an entry in the outbox is not overwritten by the pull: S008c
  decides.

## Acceptance Criteria

### Scenario: A reservation imported on one device appears on another

* **Given** two devices connected to the same calendar
* **When** a reservation is saved on the first device
* **And** the second device syncs
* **Then** the second device shows the reservation

### Scenario: A reservation deleted elsewhere disappears

* **Given** two devices showing the same reservation
* **When** its event is deleted from the calendar
* **And** the second device syncs
* **Then** the second device no longer shows it

### Scenario: A reservation added by KDE Itinerary appears

* **Given** a calendar where KDE Itinerary wrote a hotel stay
* **When** the device syncs
* **Then** the device shows the stay

## Notes

- Split from S008 (2026-11-27), validated by the maintainer (`todo`).
- 2026-11-27, implemented: `Sync.run` receives, then sends. `changes(calendar, token)`
  on the server port (`sync-collection` with `calendar-data`; a refused token — 403 on
  Nextcloud — starts over with a full listing, and an event missing from a full
  listing is gone). The store gained `received`, `removed`, `events` and the token;
  SQLite schema 3 keeps uid, href, ETag and the JSON-LD last sent on each reservation
  (migrated from 0.20.0's `calendar_events`). The screen refreshes after a run that
  received something; a detail whose reservation went away closes.
- Identity now includes the travellers: one booking for two travellers is two
  reservations, as in a KDE Itinerary batch; a batch is written back whole.
- Not done: the ETag-listing fallback for a server without `sync-collection` (Nextcloud
  has it); to add if another server needs it.
- Found on the way: Nextcloud limits how many calendars an account creates per hour
  ("Too many calendars created", 429); the real-server tests now empty "Trips" instead
  of deleting it, and a 429 is reported as "try again later" (`Problem.BUSY`).
- Size: about 400 net lines of production code (the SQLite store was rewritten), over
  the ~300 guideline; kept as one PR overnight, under the maintainer's standing "merge
  if green", and flagged in the morning recap.
