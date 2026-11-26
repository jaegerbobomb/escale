---
id: S006
title: "Connect a Nextcloud account"
epic: sync
depends_on: [S002]
status: split
estimate: M
bdd: true
updated: "2026-11-26"
adr: [4]
---

## User story

> **As a** traveller with a Nextcloud, **I want** to connect Escale to it once, **so
> that** my devices share the same trips without any other account.

## Technical description

- Preferences → Account: server URL, login, app password (v1; Nextcloud's login flow
  is an investigation issue). The password goes to the system keyring where available,
  never in plain text in the settings file.
- On connect: discover the CalDAV and WebDAV endpoints, list the user's calendars,
  let the user pick one or create "Trips"; create the `Escale/` folder if missing.
- Core adapters `nextcloud.caldav` (python `caldav`) and `nextcloud.webdav`; both
  async-wrapped.
- Integration tests against a Nextcloud container in CI.

## Acceptance Criteria

### Scenario: Connecting with valid credentials

* **Given** a reachable Nextcloud server
* **When** the user enters its URL, a login and a valid app password
* **Then** the user's calendars are listed
* **And** the account is shown as connected

### Scenario: Wrong password

* **Given** a reachable Nextcloud server
* **When** the user enters a wrong app password
* **Then** the app says the credentials were refused
* **And** nothing is saved

### Scenario: Creating the trips calendar

* **Given** a connected account with no calendar named "Trips"
* **When** the user chooses "Create a Trips calendar"
* **Then** a calendar named "Trips" exists on the server

### Scenario: The documents folder is prepared

* **Given** a connected account without an "Escale" folder
* **When** the connection completes
* **Then** the folder "Escale" exists in the user's files

## Notes

- 2026-11-24: validated by the maintainer (`todo`).
- 2026-11-26: split, validated by the maintainer (about 370 lines of production code):
  **S006a** — the core (adapters, connection, calendars, folder, integration tests
  against a Nextcloud container); **S006b** — the Preferences › Account page, the app
  password in the system keyring, the settings file.
