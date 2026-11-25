---
id: S040
title: "Train delays and platform changes"
epic: live
depends_on: [S038, S039]
status: proposed
estimate: L
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** train traveller, **I want** my timeline to show delays, cancellations and platform changes, **so that** I know before the station board does.

## Technical description

- Transitous (MOTIS) API (ADR-0005): match each train segment to a trip, fetch real-time departure, arrival, platform, cancellation.
- Card densities (S010c): delay in red, disruption card for a cancellation.
- Polling only while the trip is current and the app runs; no background service in v1.

## Acceptance Criteria

### Scenario: Delay

* **Given** a tracked train due at 10:12
* **When** Transitous reports +15 min
* **Then** the card shows 10:12 struck through and 10:27

### Scenario: Cancellation

* **Given** a tracked train
* **When** the train is reported cancelled
* **Then** the card switches to the disruption density with "Find alternatives"

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
