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
  Flightradar24 link built from the flight's callsign: the airline's **ICAO** code and
  the flight number (`AF 718` → `AFR718`).
- Flights only: Flightradar24 does not follow trains.
- Nothing is sent by Escale itself: the user chooses where the link goes (the app stays
  privacy-first).
- URL format, from a working link given by the maintainer (2026-11-24):
  `https://www.flightradar24.com/AFR718/42b64dc4`, i.e. `/<ICAO callsign>/<flight id>`.
  The flight id is Flightradar24's own id for one flight on one day: Escale cannot know
  it from the ticket. **To verify before coding**: does `/<ICAO callsign>` alone (e.g.
  `https://www.flightradar24.com/AFR718`) open that flight when it is in the air or
  about to leave? Flightradar24 cannot be reached from the build environment.
- ICAO code: kitinerary often gives only the airline's IATA code; Escale needs an IATA
  → ICAO table (source and licence to choose; must be GPL-compatible). A callsign is
  not always ICAO code + flight number: when unsure, share no link rather than a wrong
  one.

## Acceptance Criteria

### Scenario: Sharing a flight

* **Given** a flight segment AF 718
* **When** the user shares it
* **Then** the shared text holds a Flightradar24 link for AFR718

### Scenario: No link for a train

* **Given** a train segment
* **Then** no "Share flight" action is shown

## Notes

- Asked by the maintainer (2026-11-24). `proposed` until the URL format is confirmed.
