---
id: S007
title: "Map reservations to calendar events"
epic: sync
depends_on: [S005]
status: todo
estimate: S
bdd: false
updated: "2026-11-24"
adr: [4]
---

## User story

> **As a** traveller who also uses KDE Itinerary, **I want** Escale's calendar events in
> KDE Itinerary's format, **so that** either app can read them.

## Technical description

- Core domain `ical_mapping`: batch → `VEVENT` and back (`icalendar` library).
- Writes `X-KDE-KITINERARY-RESERVATION` as a compact JSON array of the batch's JSON-LD,
  a `KIT-` prefixed UID, `SUMMARY`, `DTSTART`/`DTEND` with time zones, `LOCATION`, and
  `X-ESCALE-TRIP` / `X-ESCALE-STATE` when set (`SPEC.md` § Calendar events).
- Reads events written by KDE Itinerary (fixtures from KItinerary's test data where
  their licence allows) and by Escale; an event without the property is ignored.
- Round trip is lossless for the JSON-LD.

## Acceptance Criteria

### Scenario: Round trip keeps the reservation

* **Given** a batch with one train reservation
* **When** it is written to an event and read back
* **Then** the JSON-LD is identical

### Scenario: An event written by KDE Itinerary is read

* **Given** a calendar event exported by KDE Itinerary for a hotel stay
* **When** it is read
* **Then** one lodging reservation is returned

### Scenario: A plain calendar event is ignored

* **Given** a calendar event without X-KDE-KITINERARY-RESERVATION
* **When** it is read
* **Then** no reservation is returned

## Notes

- `bdd: false`: a pure mapping, covered by unit tests; the scenarios above name them.
- 2026-11-24: validated by the maintainer (`todo`).
