---
id: S014
title: "Local store in SQLite"
epic: import
depends_on: [S004]
status: todo
estimate: S
bdd: true
updated: "2026-11-24"
adr: [4]
---

## User story

> **As a** traveller, **I want** the reservations I import to be there when I reopen
> Escale, **so that** an import is not lost when the app closes.

## Technical description

- `SqliteReservationStore` in `escale-core`, implementing the `ReservationStore` port of
  S004: reservations (raw JSON-LD, document ids) and document metadata in one SQLite
  file under the user's data directory (`$XDG_DATA_HOME/escale/` on Linux).
- Schema created on first use, with a version number for later migrations.
- The app uses it instead of the in-memory store; tests keep the in-memory one.
- SQLite stays a cache of Nextcloud (ADR-0004): this story stores, the sync stories
  (S007, S008) reconcile.
- The imported file itself is copied to `documents/<sha256>/` with its `meta.json`
  (ADR-0004 layout), so the document is still there once the original is deleted.

- Importing a ticket already stored adds nothing: same document (SHA-256), or same
  reservation (type, reference and departure time), replaces nothing and duplicates
  nothing (S005 is deferred; this is the part that matters now).

## Acceptance Criteria

### Scenario: An import survives a restart

* **Given** a confirmed import of a train ticket
* **When** the app is closed and opened again
* **Then** the reservation is still saved

### Scenario: The document is kept

* **Given** a confirmed import of a train ticket
* **When** the original file is deleted
* **Then** the document is still available under its SHA-256

### Scenario: The same ticket imported twice

* **Given** a confirmed import of a train ticket
* **When** the same file is imported and confirmed again
* **Then** the reservation is saved once

## Notes

- Split out of S004 by the maintainer (2026-11-24): S004 saves in memory only.
- 2026-11-24: validated (`todo`), with the no-duplicate rule taken from S005.
