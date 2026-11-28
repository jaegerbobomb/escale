---
id: S004
title: "Import with confirmation"
epic: import
depends_on: [S002, S003]
status: done
estimate: M
bdd: true
updated: "2026-11-24"
released_in: "0.4.0"
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

## Notes

- 2026-11-24: validated by the maintainer (`proposed` → `todo`), delivered in 0.4.0.
- Maintainer's answers before coding:
  - **Saving**: a `ReservationStore` port in the core with an in-memory implementation;
    an import is lost when the app closes. Persistence is S014 (SQLite).
  - **Trip**: the sheet shows "Add to: New trip" until trip grouping (S010).
  - **Add manually**: present and disabled until manual entry exists; enabled by S018
    (0.30.0), it opens the kinds of booking to add by hand.
- Look taken from the mockup ("Import PDF & offline ticket", step 2): a bottom sheet
  sized to its content, at most 640 px wide, the reservation in a card, "Cancel" and
  "Add to trip". Texts in English, like the rest of the app.
- Drag and drop onto the window (mockup step 1) is not in this story: "Add" and
  "Add → Import a file…" open the system file chooser. In a browser the chosen file is
  copied to a temporary folder before extraction.
- On Android and iOS (not in a browser) "Import a file" explains that tickets are read
  on Linux; the extractor is not called.
- Screenshots: `ESCALE_DEMO=1` makes `/import-found`, `/import-nothing` and
  `/import-phone` open the sheets on a synthetic ticket; only `tools/screenshots.py`
  sets it.

