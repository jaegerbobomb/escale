---
id: S008c
title: "A conflicting edit keeps the server version"
epic: sync
depends_on: [S008b]
status: done
estimate: S
bdd: true
updated: "2026-11-27"
adr: [4]
released_in: "0.22.0"
---

## User story

> **As a** traveller who edited a booking on two devices, **I want** one clear outcome
> and to be told about it, **so that** I do not lose track of which version is kept.

## Technical description

- Child of S008. When a `PUT` gets `412 Precondition Failed`, or the pull finds a
  reservation changed on the server while it has an entry in the outbox: the server
  version wins (v1, ADR-0004), the outbox entry is dropped, the local store takes the
  server's event.
- The UI says so once, as a toast: "<title> was changed on another device; that
  version is kept." (several: "N reservations were changed …").
- No merge of fields and no choice offered in v1.

## Acceptance Criteria

### Scenario: A conflicting edit keeps the server version

* **Given** a reservation edited on the server since the device last synced
* **When** the device sends its own edit of that reservation
* **Then** the device shows the server version
* **And** the user is told the reservation changed elsewhere

## Notes

- Split from S008 (2026-11-27), validated by the maintainer (`todo`).
- 2026-11-27, implemented in `sync.py`: a conflict found by the pull (the server's event
  changed while a local change waits) or by the send (`412`, the server's version then
  fetched with `get_event`) keeps the server's version (`received(..., force=True)`);
  deleted on the server wins over an edit here. `SyncReport.changed_elsewhere` lists
  the reservations, and the shell names them in the toast as the timeline does.
- The toast is a floating pill at the bottom, as libadwaita's AdwToast; the "Link
  copied" notice of S016 uses the same `toast()` now.
