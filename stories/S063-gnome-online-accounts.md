---
id: S063
title: "Use the Nextcloud account of GNOME Online Accounts"
epic: sync
depends_on: [S006b]
status: proposed
estimate: M
bdd: true
updated: "2026-11-27"
adr: [4]
---

## User story

> **As a** GNOME user whose Nextcloud is already in Settings › Online Accounts, **I
> want** Escale to offer that account, **so that** I connect it without typing a server,
> a login or an app password again.

## Technical description

- Linux only, where the `org.gnome.OnlineAccounts` D-Bus service runs. Anywhere else
  the preferences stay as S006b made them.
- Preferences › Nextcloud, not connected: above the form, one row per GOA account that
  has a calendar ("Use jane@cloud.example.org from GNOME Online Accounts"). Choosing it
  connects as S006b does, with the URL, login and password GOA gives.
- The password is asked of GOA each time it is needed; Escale does not copy it to its
  own keyring. The settings file records that the account comes from GOA (its account
  id), not a password.
- An account removed from GNOME, or whose calendar was turned off, shows as
  disconnected, with the form again.
- How to read the account (provider type, password id, file URL, Flatpak access, D-Bus
  client): issue #42, to settle before this story moves to `todo`.

## Acceptance Criteria

### Scenario: A GNOME account is offered

* **Given** a Nextcloud account in GNOME Online Accounts
* **When** the user opens the preferences
* **Then** the account is offered above the form

### Scenario: Connecting with the GNOME account

* **Given** a Nextcloud account in GNOME Online Accounts
* **When** the user chooses it in the preferences
* **Then** the user's calendars are listed
* **And** no password was typed or saved by Escale

### Scenario: Without GNOME Online Accounts

* **Given** a system without GNOME Online Accounts
* **When** the user opens the preferences
* **Then** only the form is shown

## Notes

- 2026-11-26: idea from the maintainer ("le must dans une app GNOME"); kept out of the
  sync arc (S007 → S009) on purpose.
- Investigation: issue #42.
