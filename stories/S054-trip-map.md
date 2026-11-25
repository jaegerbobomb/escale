---
id: S054
title: "Trip map"
epic: comfort
depends_on: [S010b]
status: proposed
estimate: L
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** a map of my trip with its places and segments, **so that** I see the whole journey at a glance.

## Technical description

- KDE Itinerary added a trip map view (24.12). Escale: flet-map with the trip's places and straight or routed segments.
- Tiles from an opt-in source with an offline cache (issue #23).

## Acceptance Criteria

### Scenario: Map of a trip

* **Given** a trip Paris → Lyon → Marseille
* **Then** the map shows the three places and the two segments

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
