---
id: S028
title: "Import a KDE Itinerary file"
epic: import
depends_on: [S004, S014]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** KDE Itinerary user, **I want** to bring my trips into Escale from an `.itinerary` export, **so that** I switch without losing history, documents or passes.

## Technical description

- An `.itinerary` file is a zip with `reservations/`, `batches/`, `documents/<id>/`, `passes/` (read in KDE's source, see the plan). Escale reads it with the standard `zipfile` module; no extractor needed, so it also works on Android.
- Reservations, batches, documents and pkpass go to the local store with their ids unchanged; duplicates are merged as in S005.
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
