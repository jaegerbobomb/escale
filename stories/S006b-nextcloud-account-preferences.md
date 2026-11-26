---
id: S006b
title: "Nextcloud account in the preferences"
epic: sync
depends_on: [S006a]
status: todo
estimate: S
bdd: true
updated: "2026-11-26"
adr: [4, 8]
---

## User story

> **As a** traveller with a Nextcloud, **I want** to connect Escale to it once from the
> preferences, **so that** my devices share the same trips without any other account.

## Technical description

- Child of S006. Preferences (primary menu, ADR-0008) › Account: server URL, login,
  app password (v1; Nextcloud's login flow is an investigation issue), "Connect".
- The password goes to the system keyring where available, never in plain text in
  the settings file; the URL, login and chosen calendar go to the settings file.
- Once connected: the calendars (S006a), pick one or "Create a Trips calendar"; the
  account shown as connected; "Disconnect" forgets the password.

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

## Notes

- Split from S006 (2026-11-26, validated by the maintainer).
