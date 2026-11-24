---
id: S016
title: "Share a flight to follow it live"
epic: timeline
depends_on: [S010]
status: proposed
estimate: S
bdd: true
updated: "2026-11-24"
---

## User story

> **As a** traveller, **I want** to send someone a link to follow my flight live,
> **so that** whoever picks me up knows when I land.

## Technical description

- On a flight segment: "Share flight", which shares (system share sheet, or copy) a
  Flightradar24 link built from the airline's IATA code and the flight number.
- Flights only: Flightradar24 does not follow trains.
- Nothing is sent by Escale itself: the user chooses where the link goes (the app stays
  privacy-first).
- **To verify before coding**: the Flightradar24 URL format for a flight number
  (candidates: `https://www.flightradar24.com/<IATA><number>`,
  `https://www.flightradar24.com/data/flights/<iata><number>`). Flightradar24 could not
  be reached from the build environment on 2026-11-24, and its public docs found then
  describe in-app sharing, not a URL format.

## Acceptance Criteria

### Scenario: Sharing a flight

* **Given** a flight segment AF 1234
* **When** the user shares it
* **Then** the shared text holds a Flightradar24 link for AF1234

### Scenario: No link for a train

* **Given** a train segment
* **Then** no "Share flight" action is shown

## Notes

- Asked by the maintainer (2026-11-24). `proposed` until the URL format is confirmed.
