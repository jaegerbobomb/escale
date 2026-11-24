---
id: S004
title: "Import with confirmation"
epic: import
depends_on: [S002, S003]
status: proposed
estimate: M
bdd: true
updated: "2026-11-24"
adr: [3]
---

## User story

> **As a** traveller, **I want** to review what Escale found in a file before it is
> saved, **so that** nothing wrong ends up in my trips.

## Technical description

- "Add → Import a file" opens a file picker (drag and drop onto the window if Flet
  supports it on desktop — see the investigation issue).
- A bottom sheet lists the detected reservations (type, date, route, travellers) and
  the trip they would join; "Add to trip" saves, "Cancel" discards.
- Nothing is written before confirmation. On "nothing recognised", the sheet offers
  "Add manually", pre-filled with what is known (file name, date if any).
- Android/iOS: the "Import a file" entry explains that extraction runs on Linux and the
  ticket will arrive through the sync.

## Acceptance Criteria

### Scenario: Confirming an import saves the reservation

* **Given** a ticket file with one train reservation
* **When** the file is imported
* **And** the user confirms
* **Then** the reservation is saved

### Scenario: Cancelling an import saves nothing

* **Given** a ticket file with one train reservation
* **When** the file is imported
* **And** the user cancels
* **Then** no reservation is saved

### Scenario: Nothing recognised offers manual entry

* **Given** a file with no reservation
* **When** the file is imported
* **Then** the sheet offers "Add manually"

### Scenario: Import on a phone

* **Given** the app runs on Android
* **When** the user opens "Import a file"
* **Then** the app explains that tickets are read on Linux and arrive through the sync
