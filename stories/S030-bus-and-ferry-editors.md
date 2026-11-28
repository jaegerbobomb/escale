---
id: S030
title: "Bus and ferry editors"
epic: timeline
depends_on: [S011]
status: done
bdd: true
updated: "2026-11-28"
released_in: "0.31.0"
---

## User story

> **As a** traveller, **I want** to correct or add a coach or ferry trip by hand, **so that** every mode KDE Itinerary handles is editable in Escale.

## Technical description

- The fields of KDE Itinerary's `BusEditor` and `BoatEditor` in manual mode:
  - **Bus** (`BusReservation`, `BusTrip`): bus number; departure date and time, stop
    name, platform and address; the same for the arrival; seat
    (`reservedTicket.ticketedSeat.seatNumber`); booking reference and the name it is
    under.
  - **Ferry** (`BoatReservation`, `BoatTrip`): departure date and time, terminal name and
    address; the same for the arrival; booking reference and name. KDE's ferry editor
    has no vehicle, cabin or seat, so neither has Escale's.
  - An address is KDE's `FormPlaceEditorDelegate`: street, postal code, city, region,
    country and coordinates (here latitude and longitude, as the stay editor).
- Validation, as KDE: both stop (or terminal) names and the departure time are
  required; the arrival time is optional and must be after the departure; coordinates
  must be valid.
- "Edit" on a bus or ferry detail opens its editor; "Add → Add manually…" enables
  **Bus** and **Ferry** and opens them empty (the S018 flow).

## Acceptance Criteria

### Scenario: Add a coach trip

* **Given** an empty trip list
* **When** the user adds a bus from Paris Bercy 08:00 to Lyon Perrache 13:00
* **Then** a trip to Lyon shows a bus segment with those times

### Scenario: Add a ferry crossing

* **Given** an empty trip list
* **When** the user adds a ferry from Calais 10:00 to Dover 10:30
* **Then** a trip to Dover shows a ferry segment with those times

### Scenario: A stop name is required

* **Given** the empty editor of a new bus
* **When** the user fills only the departure time
* **Then** "Save" is insensitive
* **And** the editor says the departure and arrival stops are required

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
- 2026-11-26: validated by the maintainer (`todo`), to follow the sync arc (S006–S009).
- 2026-11-28: field lists aligned with KDE Itinerary's `BusEditor.qml`, `BoatEditor.qml`
  and `FormPlaceEditorDelegate.qml` (the maintainer chose addresses "as KDE"). The ferry's
  "vehicle/cabin if present" is dropped: KDE has neither. The first scenario started
  from "an empty trip to Lyon"; Escale has no empty trips (they are grouped from
  bookings, S010a), so it starts from an empty list.
- Delivered in 0.31.0. Both editors are the generic action dialog (S029a, S061); each
  stop's address is a boxed list of its own under the stop. "Add manually…" now enables
  Bus and Ferry. The bus number is written as KDE writes it: `busNumber`, `busName`
  removed. Stop names are required on every bus or ferry, imported or not: KDE only
  checks them in manual mode, but its imported mode does not let them be edited at all.
- The address and name helpers the stay editor had are shared with these editors
  (`escale_core.editing`).
