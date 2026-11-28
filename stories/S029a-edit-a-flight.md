---
id: S029a
title: "Edit a flight"
epic: timeline
depends_on: [S011, S017b]
status: done
estimate: S
bdd: true
updated: "2026-11-28"
released_in: "0.29.0"
---

## User story

> **As a** traveller, **I want** to correct a flight by hand, **so that** a flight read
> wrongly is still right in my timeline.

## Technical description

- Child of S029. "Edit" (pencil in the header bar) on a flight's detail opens an action
  dialog (ADR-0008), as the stay editor (S017b).
- Fields, those of KDE Itinerary's `FlightEditor.qml` (read 2026-11-28): flight number
  (airline IATA code and number, e.g. "AF 718"); departure terminal, gate, boarding
  time, date and time; arrival terminal, date and time; seat; booking reference. The
  airports are shown, not edited: as in KDE Itinerary when they have an IATA code.
- Times are entered in each airport's local time and keep the offset or time zone the
  reservation had; boarding time is on the departure's day, or the day before when that
  puts it at most four hours before the departure (a flight after midnight).
- Rules, as KDE Itinerary: departure date and time required; boarding before departure;
  arrival after departure, compared in UTC; flight number `^[A-Z0-9]{2}[A-Z]? ?\d{1,5}$`.
  "Save" is insensitive while one fails, with the reason below the form.
- Saving updates the `FlightReservation` JSON-LD: `airline.iataCode`, `flightNumber`,
  `departureTerminal`, `departureGate`, `boardingTime`, `departureTime`,
  `arrivalTerminal`, `arrivalTime`, the seat (`reservedTicket.ticketedSeat.seatNumber`,
  where Escale reads it; `airplaneSeat` too when the reservation has one, as KDE
  Itinerary writes it), `reservationNumber`. Untouched fields stay as they were. The
  edit is sent to the calendar (S008a).

## Acceptance Criteria

### Scenario: Change a gate

* **Given** a flight AF 718 with gate unknown
* **When** the user sets gate "K32" and saves
* **Then** the flight's detail shows gate K32

### Scenario: Arrival before departure

* **Given** the flight editor
* **When** the arrival is set before the departure in UTC
* **Then** "Save" is disabled with the reason

## Notes

- 2026-11-28: split of S029 approved by the maintainer; the airport data investigation is
  issue #52.
- The stay editor's dialog became a generic action editor (`escale_flet.editor`), so that
  every editor to come (trains S012, buses and ferries S030) is a list of sections and
  the core's three functions (`fields_of`, `problems`, `edited`).
- Boarding time is a time of day (KDE Itinerary edits a full date-time); the "day before"
  rule keeps a 23:40 boarding for a 00:15 flight valid and still refuses 10:40 for 10:25.
- An arrival time that the reservation never had is entered in the departure's offset:
  without the airport table (S029b) Escale does not know the arrival airport's zone.
