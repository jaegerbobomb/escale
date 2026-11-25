---
id: S047
title: "Station and airport map"
epic: stations
depends_on: [S039]
status: proposed
estimate: XL
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller in a big station, **I want** a floor map with my platform, exits, lifts and shops, **so that** I find my way without the station's own app.

## Technical description

- KDE Itinerary draws "train station and airport per-floor maps based on OpenStreetMap data" (KOSMIndoorMap, C++). No Python equivalent known: render OSM indoor data (levels, platforms, amenities) fetched as vector data, opt-in.
- Highlights the platform section of the reservation when known (S048).
- Too big for one story: split before work starts.

## Acceptance Criteria

### Scenario: Platform highlighted

* **Given** a train leaving from platform 7
* **When** the user opens the station map
* **Then** the floor with platform 7 is shown and the platform is highlighted

## Notes

- Rendering library to investigate (issue to open).
- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
