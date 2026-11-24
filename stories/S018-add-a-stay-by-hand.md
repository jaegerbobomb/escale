---
id: S018
title: "Add a stay by hand"
epic: import
depends_on: [S017]
status: todo
estimate: S
bdd: true
updated: "2026-11-24"
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
