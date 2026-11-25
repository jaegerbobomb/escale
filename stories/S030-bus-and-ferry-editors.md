---
id: S030
title: "Bus and ferry editors"
epic: timeline
depends_on: [S011]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** to correct or add a coach or ferry trip by hand, **so that** every mode KDE Itinerary handles is editable in Escale.

## Technical description

- Bus (`BusReservation`): line/name, departure and arrival stop and time, seat. Ferry (`BoatReservation`): departure and arrival terminal and time, vehicle/cabin if present. Field lists to align with KDE Itinerary's editors.
- "Add → Bus" and "Add → Ferry" open them empty.

## Acceptance Criteria

### Scenario: Add a coach trip

* **Given** an empty trip to Lyon
* **When** the user adds a bus from Paris Bercy 08:00 to Lyon Perrache 13:00
* **Then** the trip shows a bus segment with those times

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
