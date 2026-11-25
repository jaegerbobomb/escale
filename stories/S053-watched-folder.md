---
id: S053
title: "Watched folder on Linux"
epic: comfort
depends_on: [S003, S004]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** Linux user, **I want** Escale to pick up tickets I save in a folder, **so that** downloading a ticket is enough.

## Technical description

- Preference: one folder (default `~/Downloads`, off by default). New PDF, pkpass or `.eml` files are extracted; any reservation found raises a confirmation, never a silent import.

## Acceptance Criteria

### Scenario: New ticket

* **Given** the watched folder is on
* **When** a ticket PDF is saved in it
* **Then** Escale offers to import it

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
