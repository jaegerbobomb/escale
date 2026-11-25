---
id: S042
title: "Find alternative connections"
epic: live
depends_on: [S040]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller with a cancelled train or a missed connection, **I want** to pick another connection and put it in my trip, **so that** I still arrive, and my timeline stays true.

## Technical description

- KDE Itinerary: "selection of alternative train connections on unbound tickets or on missed connections". Same in Escale through Transitous journey search, from the disruption card or the segment menu.
- The chosen journey replaces the segment as "planned" (not a ticket); the old one is kept, marked replaced.

## Acceptance Criteria

### Scenario: Replace a cancelled train

* **Given** a cancelled train
* **When** the user picks an alternative
* **Then** the timeline shows the new connection as planned

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
