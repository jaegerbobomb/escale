---
id: S007
title: "Map reservations to calendar events"
epic: sync
depends_on: [S014]
status: done
estimate: S
bdd: false
updated: "2026-11-26"
adr: [4]
released_in: "0.19.0"
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
- 2026-11-26, option A chosen by the maintainer: no dependency on S005 (deferred). Until
  batches exist, one event holds one reservation — the `X-KDE-KITINERARY-RESERVATION`
  array has a single element, which KItinerary reads as a batch of one. Batches come
  back with S005.
- 2026-11-26, implemented in `escale_core/ical_mapping.py` (`new_entry`, `to_event`,
  `to_ics`, `from_event`, `entries_in`), after KItinerary's `CalendarHandler` (read in
  its source, not copied): `SUMMARY` worded as KItinerary does ("Train 5186 from … to …",
  "Hotel reservation: …"); a stay is an all-day event from the check-in date to the
  check-out date, `TRANSP:TRANSPARENT`; other reservations keep their time zone
  (`TZID` and `VTIMEZONE`), a bare UTC offset is written in UTC.
- The payload is escaped as iCalendar TEXT (`\,`, `\;`), as libical writes it; reading
  accepts it raw too, as in some of KItinerary's test data.
- Fixtures: KItinerary's `autotests/calendarhandlerdata/hotel.ics` and `train.ics`
  (CC0-1.0).
- Not in S007: KItinerary's `DESCRIPTION` and `GEO`, and the "Canceled:" prefix; the
  documents (`subjectOf`) come with S009. Escale writes the JSON-LD as stored, without
  adding `@context`.
