---
id: S032
title: "Group bookings into outings"
epic: outings
depends_on: [S010a, S031]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** city dweller, **I want** a concert and the dinner before it to form one outing, **so that** my evenings are as easy to follow as a trip.

## Technical description

- Rule (mockup "Sorties"): bookings on the same day, without a stay, close in time (gap ≤ 4 h, to tune) and in place, form a `Trip` of kind `outing`.
- Colour `#9141ac`; name built from its events ("Concert + dinner").
- The user can turn an outing into a trip and back (S038).

## Acceptance Criteria

### Scenario: Concert and dinner

* **Given** a restaurant at 19:00 and a concert at 21:00 the same day, 1 km apart
* **Then** they form one outing named "Dinner + concert"

### Scenario: A hotel makes it a trip

* **Given** the same bookings and a stay that night
* **Then** they form a trip, not an outing

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
