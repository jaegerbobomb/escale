---
id: S008b
title: "Receive changes from the calendar"
epic: sync
depends_on: [S008a]
status: proposed
estimate: M
bdd: true
updated: "2026-11-27"
adr: [4]
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

- Split from S008 (2026-11-27), proposed.
