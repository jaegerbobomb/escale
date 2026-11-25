---
id: S045
title: "Update passes"
epic: live
depends_on: [S039]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller with a boarding pass, **I want** my pkpass to update itself when the issuer allows it, **so that** gate and seat stay right.

## Technical description

- Passes with `webServiceURL` and `authenticationToken`: fetch the latest version (Apple Wallet web service protocol, GET only, no device registration in v1).
- Part of "Refresh" (S038).

## Acceptance Criteria

### Scenario: Gate change

* **Given** an updatable boarding pass
* **When** the issuer serves a new version with gate K40
* **Then** the pass shows gate K40

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
