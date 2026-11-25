---
id: S031
title: "Event, restaurant and car editors"
epic: timeline
depends_on: [S011]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** to correct or add an event, a table or a rental car, **so that** my evenings and road trips sit in the same timeline as trains.

## Technical description

- Event (`EventReservation`): name, venue, address, start, end, seat. Restaurant (`FoodEstablishmentReservation`): name, address, time, party size. Rental car (`RentalCarReservation`): company, pick-up and drop-off place and time, car.
- A rental car shows two cards (pick-up, drop-off), as in KDE Itinerary.
- "Add → Event / Restaurant / Rental car".

## Acceptance Criteria

### Scenario: A rental car spans the trip

* **Given** a rental car picked up on 3 July and dropped off on 9 July
* **Then** the timeline shows a pick-up card on 3 July and a drop-off card on 9 July

### Scenario: Add a restaurant

* **Given** a trip to Paris
* **When** the user adds a table for 4 at "Chez Paul" at 20:00
* **Then** the timeline shows it at 20:00 with the address

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
