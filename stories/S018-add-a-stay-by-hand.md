---
id: S018
title: "Add a stay by hand"
epic: import
depends_on: [S017]
status: done
bdd: true
updated: "2026-11-28"
released_in: "0.30.0"
---

## User story

> **As a** traveller who booked by phone or on a site Escale cannot read, **I want** to
> add my stay myself, **so that** it is in my trip like any imported booking.

## Technical description

- "Add → Add manually…" offers the kinds of booking; this story enables **Stay**. It
  opens the editor of S017, empty, with the same validation.
- The import sheet's "Add manually" (S004, disabled until now) opens the same editor
  when the file was a stay or when the user picks "Stay".
- The saved stay is a `LodgingReservation` JSON-LD like an imported one, with no
  document; trip grouping (S010a) places it.
- Other kinds (train, event, restaurant…) stay disabled until their editors exist.

## Acceptance Criteria

### Scenario: Adding a stay

* **Given** an empty trip list
* **When** the user adds a stay "Hôtel du Nord", Paris, from 8 July 15:00 to 10 July 11:00
* **Then** the stay is saved
* **And** a trip to Paris shows it

### Scenario: Cancelling adds nothing

* **Given** the empty editor of a new stay
* **When** the user fills the name and cancels
* **Then** no stay is saved

### Scenario: Manual entry after a failed import

* **Given** a file with no reservation was imported
* **When** the user chooses "Add manually" then "Stay"
* **Then** the editor of a new stay is shown

## Notes

- 2026-11-24: validated by the maintainer (`todo`).
- Delivered in 0.30.0. "Add manually…" opens an action dialog (a bottom sheet under
  450 px) listing Stay, Flight, Train, Bus, Ferry, Event and Restaurant; only Stay is
  sensitive. Flight waits for the airport table (S029b), bus and ferry for S030.
- The editor is the stay editor (S017b) titled "New Stay". The saved stay has no
  document; it opens in its trip: in "Current" when that is the active trip, else as the
  trip opened from "My trips".
- Time zone: a booking added by hand has no stored zone, so its times take the device's
  UTC offset on that day (`datetime.astimezone()`, right for summer and winter time).
  KDE Itinerary works the zone out from the place; Escale has no geocoder yet.
- "Add manually" after a failed import opens the same chooser; nothing is pre-filled
  (S004 mentioned the file name and a date: the extraction found neither), and the file
  is not attached to the stay.
- The chooser and the editor change presentation when the window crosses 450 px.
