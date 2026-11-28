---
id: S028
title: "Import a KDE Itinerary file"
epic: import
depends_on: [S004, S014]
status: done
estimate: M
bdd: true
updated: "2026-11-28"
released_in: "0.27.0"
---

## User story

> **As a** KDE Itinerary user, **I want** to bring my trips into Escale from an `.itinerary` export, **so that** I switch without losing history, documents or passes.

## Technical description

- An `.itinerary` file is a zip with `reservations/`, `documents/<id>/`, `passes/` and `custom/` (read in KDE's source: KItinerary's `File`, KDE Itinerary's `importexport.cpp`). Escale reads it with the standard `zipfile` module; no extractor needed, so it also works on Android.
- Reservations and documents go to the local store with their ids unchanged; duplicates are merged as in S005. Passes (pkpass) are listed as not imported until Escale reads passes (S055).
- Program memberships, health certificates and settings in the archive are ignored in v1 and listed in the confirmation ("not imported").

## Acceptance Criteria

### Scenario: A full export

* **Given** an `.itinerary` file with two trips and their PDFs
* **When** the user imports it
* **Then** the confirmation lists the reservations
* **And** after confirming, both trips appear with their documents

### Scenario: A file imported twice

* **Given** the same `.itinerary` file was already imported
* **When** it is imported again
* **Then** nothing is duplicated

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
- 2026-11-26: validated by the maintainer (`todo`), to follow the sync arc (S006–S009).
- 2026-11-28: KDE's source (`src/lib/file.cpp` in KItinerary, `src/app/importexport.cpp`
  and `bundle-constants.h` in KDE Itinerary, master, read on the GitHub mirror) shows no
  `batches/` folder: KDE Itinerary writes each reservation on its own and batches them
  again on import; Escale's store does the same by identity. Trip groups, transfers and
  live data (`custom/org.kde.itinerary/…`) are ignored without being listed: Escale
  groups trips itself. Passes are listed as not imported: Escale reads no pkpass yet.
- Document ids are kept as they are in the file. KDE Itinerary names a document by the
  SHA-256 of its content (as checked for S009a), so S009b's check of a download against
  its id holds; a file with other ids would import, but those documents would not
  download on other devices.
- The confirmation sheet now scrolls: an export can hold many reservations.
