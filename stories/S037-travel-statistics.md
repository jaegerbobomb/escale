---
id: S037
title: "Travel statistics"
epic: browse
depends_on: [S035]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** to see how far and how I travelled, **so that** I can watch the environmental impact of my trips.

## Technical description

- Per year and per trip (KDE Itinerary has both): distance and number of trips by mode, CO₂ estimate, nights, countries.
- Computed locally from the reservations (great-circle distance, emission factors per mode from a cited source).

## Acceptance Criteria

### Scenario: Year summary

* **Given** two train trips and one flight in 2026
* **Then** the 2026 statistics show the distance by mode and a CO₂ estimate

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
