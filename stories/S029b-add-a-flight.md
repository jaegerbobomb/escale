---
id: S029b
title: "Add a flight by hand"
epic: timeline
depends_on: [S029a]
status: todo
estimate: S
bdd: true
updated: "2026-11-28"
---

## User story

> **As a** traveller, **I want** to add a flight that no ticket file gave Escale, **so
> that** my timeline has it.

## Technical description

- Child of S029. "Add → Flight" opens the flight editor (S029a) empty, with the
  departure and arrival airports chosen by IATA code; each airport gives its name and
  time zone, so that times are entered in local time.
- The airport table (IATA code, name, time zone) comes from a data source chosen by an
  investigation issue, GPL-3.0-compatible, before this story is coded.
- Saving adds a `FlightReservation` to the store and sends it to the calendar.

## Acceptance Criteria

### Scenario: Add a flight

* **Given** the flight editor opened from "Add → Flight"
* **When** the user enters AF 718 from CDG to LHR with its times and saves
* **Then** the flight is in the timeline with Paris and London times

## Notes

- 2026-11-28: split of S029 approved by the maintainer; waits for the airport data
  investigation.
