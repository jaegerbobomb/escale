---
id: S050
title: "Time zone and DST changes"
epic: comfort
depends_on: [S010b]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** the timeline to tell me when the clock changes, **so that** I do not miss a train after a time change.

## Technical description

- Times shown in the place's time zone; a marker when the time zone changes and when a DST transition falls inside the trip (KDE Itinerary does both).

## Acceptance Criteria

### Scenario: DST during a trip

* **Given** a trip from 24 to 27 October 2026 in Paris
* **Then** the timeline shows a "Clocks go back 1 h" marker on 25 October

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
