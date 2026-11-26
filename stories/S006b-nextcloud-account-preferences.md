---
id: S006b
title: "Nextcloud account in the preferences"
epic: sync
depends_on: [S006a]
status: done
estimate: S
bdd: true
updated: "2026-11-26"
adr: [4, 8]
released_in: "0.18.0"
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
- Size: about 600 raw lines of production code (the preferences screen alone about 250),
  over the ~300 guideline; kept as one PR at the maintainer's choice (2026-11-26).
- The preferences are libadwaita's AdwPreferencesDialog: a title and a close button, no
  Save, changes apply at once; a bottom sheet under 450 px, as the stay editor. They are
  opened from a new primary menu (☰), last in the header bar of the three main views
  (ADR-0008); a detail or the ticket has none.
- "Connect" stays insensitive until the server, the login and the app password are
  filled in. Nothing is saved before the server accepts them.
- Keyring: the `keyring` library (MIT; Secret Service on Linux through `secretstorage`
  and `jeepney`, installed on Linux only). Without a keyring the password stays in
  memory until the app quits, and the preferences say it will be asked again.
- Settings file: `$XDG_CONFIG_HOME/escale/settings.json`, key `nextcloud` (`url`,
  `login`, `calendar` = the chosen calendar's URL); other keys are kept on save.
- "Disconnect" forgets the password and the account on the device; nothing is deleted on
  the server.
- An account restored at start-up is not checked against the server until the
  preferences are opened (they then load its calendars).
