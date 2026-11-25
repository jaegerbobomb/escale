---
id: S051
title: "Weather forecast"
epic: comfort
depends_on: [S039, S010b]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** the weather at my destination on arrival day, **so that** I pack and plan accordingly.

## Technical description

- Forecast for each place and day within the forecast range; KDE Itinerary uses the MET Norway API (to confirm). Opt-in source (S039), cached.

## Acceptance Criteria

### Scenario: Forecast shown

* **Given** the weather source is on and an arrival in Lyon tomorrow
* **Then** the arrival card shows tomorrow's forecast for Lyon

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
