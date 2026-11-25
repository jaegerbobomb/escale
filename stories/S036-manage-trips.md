---
id: S036
title: "Rename, merge, split, delete trips"
epic: browse
depends_on: [S035]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** to fix how my bookings were grouped, **so that** the automatic grouping never traps me.

## Technical description

- Actions on a trip: rename (KDE Itinerary 25.04 "trips can now be renamed"), merge with the previous or next trip, split before a segment, delete (with its reservations, after confirmation), move a reservation to another trip.
- Choices are stored in `X-ESCALE-TRIP` so the grouping keeps them and they sync.

## Acceptance Criteria

### Scenario: Rename

* **Given** a trip "Trip to Lyon"
* **When** the user renames "Trip to Lyon" to "Wedding"
* **Then** the trip is called "Wedding" on every device after sync

### Scenario: Split

* **Given** a trip with an outbound and a return two weeks later
* **When** the user splits before the return
* **Then** there are two trips, and a new import does not merge them back

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
