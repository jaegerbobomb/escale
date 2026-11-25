---
id: S044
title: "Plan a train journey"
epic: live
depends_on: [S039]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** to search a connection and add it to a trip before buying, **so that** I can plan with Escale, not only record.

## Technical description

- Four-screen flow of the mockup (from, to, when, results), pre-filled from the trip; current location as a start.
- Added as "planned" (no ticket); importing the ticket later merges with it.

## Acceptance Criteria

### Scenario: Planned then bought

* **Given** a planned train Paris → Lyon at 10:00
* **When** the matching ticket is imported
* **Then** the planned segment becomes the booked one

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
