---
id: S049
title: "Country change card"
epic: comfort
depends_on: [S010b]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller crossing a border, **I want** a card telling me what changes, **so that** I am not caught out by plugs, currency or driving side.

## Technical description

- Card between segments when the country changes: currency (with a converter, KDE 2025; rates opt-in), power plugs, driving side, time zone.
- Rewrite of `KItinerary::CountryInformation` as a local table (vision).

## Acceptance Criteria

### Scenario: Paris to London

* **Given** a train Paris → London
* **Then** a card before arrival says: GBP, plug type G, drive on the left, -1 h

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
