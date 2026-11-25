---
id: S039
title: "One switch per network source"
epic: live
depends_on: []
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** privacy-minded user, **I want** to choose which online services Escale may call, **so that** nothing leaves my device without my consent.

## Technical description

- Preferences → Online services: one switch per source (Transitous, weather, operator imports, pkpass updates, Nominatim, Overpass, Google links, map tiles, Matrix), with what is sent and to whom.
- Every adapter that touches the network checks its switch; off by default except what the maintainer decides (to decide).

## Acceptance Criteria

### Scenario: A source turned off

* **Given** the weather source is off
* **Then** no request is made to the weather service
* **And** the timeline shows no weather

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
