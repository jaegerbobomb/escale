---
id: S008a
title: "Send local reservations to the calendar"
epic: sync
depends_on: [S006b, S007, S014]
status: proposed
estimate: M
bdd: true
updated: "2026-11-27"
adr: [4]
---

## User story

> **As a** traveller who imports a ticket on my laptop, **I want** it written to my
> Nextcloud calendar, **so that** my other devices and KDE Itinerary can get it.

## Technical description

- Child of S008. The local store keeps, per reservation, the event `UID` and the last
  known `ETag`, and an outbox of what has not reached the server yet (added, changed).
- Core service `sync`, push half: for each outbox entry, `PUT` the event of S007 to the
  calendar chosen in the preferences — `If-None-Match: *` for a new one, `If-Match:
  <etag>` for a change — then store the new ETag and clear the entry.
- When the push runs: after an import or an edit, at start, and every 10 minutes while
  the app is open. No account, no calendar chosen, or no network: the outbox waits, the
  app works as before.
- A `412` is left in the outbox for S008c; until then it is retried at the next push.
- Deleting a reservation is not in the app yet (S036); when it comes, it goes through
  the same outbox (`DELETE` with `If-Match`).
- Tested against the fake Nextcloud, and against the real one in the CI's `nextcloud`
  job.

## Acceptance Criteria

### Scenario: An imported reservation reaches the calendar

* **Given** a device connected to a calendar
* **When** a reservation is saved on the device
* **Then** the calendar has an event holding that reservation

### Scenario: An edit made offline is sent later

* **Given** a device without network
* **When** the user edits a reservation
* **And** the network comes back
* **Then** the edit is on the server

### Scenario: Without an account nothing is sent

* **Given** a device with no Nextcloud account
* **When** a reservation is saved on the device
* **Then** the reservation is kept on the device only

## Notes

- Split from S008 (2026-11-27), proposed.
