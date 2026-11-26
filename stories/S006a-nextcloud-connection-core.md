---
id: S006a
title: "Nextcloud connection (core)"
epic: sync
depends_on: [S002]
status: done
estimate: S
bdd: true
updated: "2026-11-26"
released_in: "0.17.0"
adr: [4]
---

## User story

> **As a** traveller with a Nextcloud, **I want** Escale to check my account and find
> my calendars and files, **so that** my devices can share the same trips.

## Technical description

- Child of S006: the core part, no UI (S006b).
- Core adapters (ADR-0004, SPEC § External contracts): `nextcloud.caldav` (python
  `caldav`) and `nextcloud.webdav` (HTTP `PROPFIND` / `MKCOL`), wrapped for asyncio.
  Endpoints from the server URL: `remote.php/dav` for CalDAV, the user's
  `remote.php/dav/files/<login>/` for files.
- Service `connect(url, login, app password)`: checks the credentials, lists the
  user's calendars (name, URL, whether it holds events), and makes sure the `Escale/`
  folder exists. `create_trips_calendar()` creates a calendar named "Trips".
- Errors as results the UI can say: credentials refused, server not reachable, not a
  Nextcloud (no DAV endpoint).
- A fake of the adapters for the service tests; integration tests against a real
  Nextcloud in a container, run locally when Docker is there and in CI as a job of
  their own (`ESCALE_NEXTCLOUD_URL`).

## Acceptance Criteria

### Scenario: Connecting with valid credentials

* **Given** a reachable Nextcloud server
* **When** Escale connects with a login and a valid app password
* **Then** the user's calendars are listed

### Scenario: Wrong password

* **Given** a reachable Nextcloud server
* **When** Escale connects with a wrong app password
* **Then** the result says the credentials were refused

### Scenario: Creating the trips calendar

* **Given** a connected account with no calendar named "Trips"
* **When** the trips calendar is created
* **Then** a calendar named "Trips" exists on the server

### Scenario: The documents folder is prepared

* **Given** an account without an "Escale" folder
* **When** Escale connects
* **Then** the folder "Escale" exists in the user's files

## Notes

- Split from S006 (2026-11-26, validated by the maintainer).
- Delivered in 0.17.0. `escale_core/nextcloud.py` (service, `Calendar`, `Problem`,
  `endpoints`), `adapters/nextcloud_dav.py` (one adapter for CalDAV and WebDAV: both go
  through `caldav`'s `DAVClient`, which does PROPFIND and MKCOL too, so no second HTTP
  library), `adapters/fake_nextcloud.py`.
- `caldav` 3.7 (GPL-3.0-or-later OR Apache-2.0); it brings `niquests`, `lxml` and
  `icalendar`. `lxml` is compiled: whether it builds for Android is to check with S013.
- Errors: `AuthorizationError` → credentials refused; connection errors and timeouts
  (20 s) → unreachable; any other DAV error (a 405 on PROPFIND, …) → not a Nextcloud.
- Tested against Nextcloud 31.0.14 (`nextcloud:31-apache`) in Docker in the build
  environment and in the CI job `nextcloud`; how to run them:
  `docs/how-to/run-the-nextcloud-tests.md`.
