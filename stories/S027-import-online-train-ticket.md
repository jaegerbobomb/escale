---
id: S027
title: "Import an online train ticket"
epic: import
depends_on: [S004, S041]
status: proposed
estimate: L
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** SNCF or Deutsche Bahn customer, **I want** to fetch my ticket from its booking reference and name, **so that** I do not need the e-mail or the PDF.

## Technical description

- KDE Itinerary "added support for importing Deutsche Bahn and SNCF online tickets" (23.08 release notes). That code is in the Itinerary app (C++), not in `kitinerary-extractor`: Escale has to call the same endpoints itself.
- Form: operator, booking reference, last name. One request to the operator, only when the user submits, and only if the source is enabled (S041).
- The answer (JSON or ticket document) goes through the extractor on Linux, then the confirmation sheet (S004).
- These endpoints are not public APIs: they can change or close. Read KDE's implementation first (licence: reuse only what is GPL-compatible).
- Also from KDE: importing Deutsche Bahn journey sharing links (24.x).

## Acceptance Criteria

### Scenario: SNCF reference

* **Given** the SNCF source is enabled
* **When** the user enters a valid booking reference and last name
* **Then** the confirmation sheet shows the trains of that booking

### Scenario: Source disabled

* **Given** the SNCF source is disabled
* **Then** the online import form says why it is unavailable and links to the preferences

## Notes

- Needs an investigation issue on the endpoints before it can be `todo`.
- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
