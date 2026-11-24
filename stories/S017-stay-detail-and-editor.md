---
id: S017
title: "Stay detail and editor"
epic: timeline
depends_on: [S010b]
status: proposed
estimate: M
bdd: true
updated: "2026-11-24"
---

## User story

> **As a** traveller, **I want** to see and correct everything about where I sleep,
> **so that** the address, the times and the booking reference are right when I arrive.

## Technical description

- A stay (`LodgingReservation`) opens from its card in the timeline onto a detail page:
  name, address, check-in and check-out (date and time, with the place's time zone),
  room details, contact (telephone, e-mail, website), booking (reference, under name,
  cancelled or not), documents.
- "Edit" shows the fields of KDE Itinerary's `HotelEditor` (read in its source,
  2026-11-24): name; address (street, postal code, city, region, country, coordinates);
  check-in; check-out; description (`lodgingUnitDescription`); contact (telephone,
  e-mail, website); booking (reference, under name); the trip it belongs to.
- Validation as in KDE Itinerary: the name is required, check-in and check-out are
  required, check-out is after check-in.
- Saving updates the raw JSON-LD (schema.org `LodgingReservation` / `LodgingBusiness`)
  in the local store; the sync stories send it later.
- Telephone, e-mail and website are actionable (call, write, open), through the system.
- **Manage the booking.** When the JSON-LD carries a link to the booking — schema.org
  `potentialAction` / `modifyReservationUrl` or the reservation's `url`, as KItinerary
  extracts from Booking.com or Airbnb confirmations — the detail shows "Manage booking
  on <site>", which opens it in the browser. Escale never logs into those sites.
- The navigation to the detail reuses S011's when it exists; until then the detail
  opens as a page with a back button.

## Acceptance Criteria

### Scenario: The detail of a stay

* **Given** a stored stay at "The Hoxton, Holborn" from 8 July 15:00 to 10 July 11:00
* **When** the user opens its card
* **Then** the detail shows the name, the address, the check-in and the check-out

### Scenario: Correcting the check-out time

* **Given** the detail of a stay with check-out at 11:00
* **When** the user edits the check-out to 12:00 and saves
* **Then** the detail shows check-out at 12:00

### Scenario: The booking can be managed on its site

* **Given** a stay imported from a Booking.com confirmation with a link to manage the booking
* **When** the user opens its detail
* **Then** a "Manage booking on Booking.com" action is shown

### Scenario: A check-out before the check-in is refused

* **Given** the editor of a stay with check-in on 8 July
* **When** the user sets the check-out to 7 July
* **Then** "Save" is disabled
* **And** the editor says the check-out must be after the check-in

### Scenario: A stay without a name is refused

* **Given** the editor of a stay
* **When** the user empties the name
* **Then** "Save" is disabled

## Notes

- Proposed 2026-11-24, as the prerequisite of importing a place shared from Google Maps
  (S019): a shared place becomes a stay, so stays must be editable first.
