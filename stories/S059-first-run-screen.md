---
id: S059
title: "First-run screen"
epic: packaging
depends_on: [S006]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** new user, **I want** a first screen that tells me what Escale needs, **so that** I start in a minute.

## Technical description

- Welcome, connect Nextcloud (S006) or "Use without sync", then the online-services switches (S039).

## Acceptance Criteria

### Scenario: Skip sync

* **Given** a first launch
* **When** the user chooses "Use without sync"
* **Then** the empty timeline is shown and Preferences → Account stays available

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
