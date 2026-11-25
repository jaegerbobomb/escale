---
id: S017b
title: "Stay editor"
epic: timeline
depends_on: [S017a]
status: done
estimate: M
bdd: true
updated: "2026-11-25"
released_in: "0.14.0"
---

## User story

> **As a** traveller, **I want** to correct everything about where I sleep, **so that**
> the address, the times and the booking reference are right when I arrive.

## Technical description

- Child of S017. "Edit" on a stay's detail (S017a) shows the fields of KDE Itinerary's
  `HotelEditor` (read in its source, 2026-11-24): name; address (street, postal code,
  city, region, country, coordinates); check-in; check-out; description
  (`lodgingUnitDescription`); contact (telephone, e-mail, website); booking (reference,
  under name); the trip it belongs to.
- Validation as in KDE Itinerary: the name is required, check-in and check-out are
  required, check-out is after check-in.
- Saving updates the raw JSON-LD (schema.org `LodgingReservation` / `LodgingBusiness`)
  in the local store; the sync stories send it later.

## Acceptance Criteria

### Scenario: Correcting the check-out time

* **Given** the detail of a stay with check-out at 11:00
* **When** the user edits the check-out to 12:00 and saves
* **Then** the detail shows check-out at 12:00

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

- Split from S017 (2026-11-25, validated by the maintainer). The detail is S017a.
- Delivered in 0.14.0. "Edit" on the stay's detail opens the editor in its place:
  groups Hotel, Address, Stay, Contact, Booking. Dates and times are text fields
  (`YYYY-MM-DD`, `HH:MM`) in the place's own time; a saved time keeps the stored time
  zone (kitinerary's `QDateTime` with its `timezone`, else the stored offset), so a
  winter date gets the winter offset.
- Only the fields the user changed are written back; the rest of the JSON-LD stays as
  imported (a `Person`'s e-mail, an `addressCountry` object…). An empty field removes
  its key. "Under the name of" takes several names separated by commas.
- Validation, as in KDE Itinerary: name, check-in and check-out required, check-out
  after check-in; plus valid dates and times, and both coordinates or none, in range.
  "Save" is disabled and the reasons are listed under the form.
- `ReservationStore.replace(old, new)`, in memory and in SQLite (the row keeps its id;
  its identity follows a changed booking reference).
- Not done: "the trip it belongs to". Trips are computed by grouping (S010a); choosing
  one by hand comes with managing trips (S036, proposed).
- Size: about 415 lines of production code, over the ~300-line limit. The maintainer
  chose to keep it as one PR (2026-11-25) rather than split it once written.
