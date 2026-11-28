---
id: S029
title: "Flight segment editor"
epic: timeline
depends_on: [S011]
status: split
estimate: S
bdd: true
updated: "2026-11-28"
---

## User story

> **As a** traveller, **I want** to correct or add a flight by hand, **so that** a flight read wrongly, or not read at all, is still right in my timeline.

## Technical description

- Fields of KDE Itinerary's flight editor (read its QML before implementing): airline and flight number; departure airport, terminal, gate, boarding time, departure time; arrival airport, terminal, arrival time; seat; booking reference.
- Airports by IATA code with their time zone (table to choose, GPL-compatible).
- "Add → Flight" opens the same editor empty.
- Saving updates the JSON-LD (`FlightReservation`) as S012 does for trains.

## Acceptance Criteria

### Scenario: Change a gate

* **Given** a flight AF 718 with gate unknown
* **When** the user sets gate "K32" and saves
* **Then** the flight card shows gate K32

### Scenario: Arrival before departure

* **Given** the flight editor
* **When** the arrival is set before the departure in UTC
* **Then** "Save" is disabled with the reason

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
- 2026-11-26: validated by the maintainer (`todo`), to follow the sync arc (S006–S009).
- 2026-11-28: split approved by the maintainer: S029a (edit an existing flight, airports
  read-only) now; S029b (airport table by IATA code with time zones, "Add → Flight")
  after an investigation chooses the airport data source.
