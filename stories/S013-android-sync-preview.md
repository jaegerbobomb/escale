---
id: S013
title: "Android build listing synced reservations"
epic: sync
depends_on: [S008, S009]
status: proposed
estimate: S
bdd: false
updated: "2026-11-24"
adr: [1, 4]
---

## User story

> **As a** maintainer, **I want** an early Android build that lists the synced
> reservations, **so that** the riskiest part — DAV libraries in Flet on Android — is
> proven before the rich screens are built.

## Technical description

- `flet build apk` for `escale-flet` in CI (artifact, not published).
- The app connects to the account (S006), syncs (S008) and lists reservations in a
  plain list; opening one shows its document (S009).
- Record in `## Notes` any dependency that needed a workaround on Android.

## Acceptance Criteria

### Scenario: The APK is built in CI

* **Given** a pull request on `main`
* **When** CI runs
* **Then** an APK artifact is produced

### Scenario: Synced reservations show on a phone

* **Given** an account with three reservations synced from Linux
* **When** the APK is installed and connected to that account
* **Then** the three reservations are listed

## Notes

- `bdd: false`: verified by CI and by a manual check on a device, reported in the PR.
