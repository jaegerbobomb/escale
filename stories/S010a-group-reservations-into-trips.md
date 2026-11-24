---
id: S010a
title: "Group reservations into trips"
epic: timeline
depends_on: [S014]
status: done
estimate: M
bdd: true
updated: "2026-11-24"
released_in: "0.6.0"
adr: [7]
---

## User story

> **As a** traveller, **I want** my bookings grouped into trips and outings, **so that**
> each journey shows up as one thing.

## Technical description

- Core `trips`: from the stored reservations, build `Trip`s (kind `trip` or `outing`),
  each with a name, a start, an end and its reservations in time order.
- A trip starts with a reservation and goes on while the next one starts within a day
  of the trip's end, or until the traveller is back where the trip started (an arrival
  at the first departure's place), within 30 days.
- An outing: same calendar day, no lodging, no long-distance transport (train, flight,
  bus, boat).
- Name of a trip: the town of its lodging, else of its first arrival. Name of an
  outing: its events' names joined with " + ".
- `active_trip(trips, now)`: the trip in progress, else the next one.
- Times come from the JSON-LD: departure/arrival for transport, check-in/check-out for
  lodging, start/end for events, start for restaurants. Reservations without any time
  are left out.

## Acceptance Criteria

### Scenario: A return trip becomes one trip

* **Given** a train from Paris to London on 8 July, a hotel in London from 8 to 10 July, and a train back on 10 July
* **When** the reservations are grouped
* **Then** they form one trip named "London"

### Scenario: A dinner and a concert become an outing

* **Given** a restaurant booking at 19:30 and a concert ticket at 21:00 in Paris on the same evening
* **When** the reservations are grouped
* **Then** they form one outing

### Scenario: Two journeys a week apart stay apart

* **Given** a return train to Lyon on 1 July and a return train to Lille on 8 July
* **When** the reservations are grouped
* **Then** they form two trips, "Lyon" and "Lille"

### Scenario: The current trip is the one in progress, else the next

* **Given** a trip from 8 to 10 July and another from 20 to 22 July
* **When** it is 9 July
* **Then** the active trip is the first one

## Notes

- Child of S010 (split validated by the maintainer, 2026-11-24).
- A named or forced grouping (`X-ESCALE-TRIP`) comes with the calendar sync (S007).
- Simpler than KDE Itinerary's `TripGroupManager`: no home location yet (Settings).
- Delivered in 0.6.0 (`escale_core.trips`). "Back where it started" compares towns
  (`address.addressLocality`, else the place's name): Paris Gare de Lyon and Paris Nord
  match when kitinerary gives their town, not otherwise. A trip waiting for its way back
  gives up after 30 days.
- Not shown anywhere yet: S010b puts the active trip in "Current".
