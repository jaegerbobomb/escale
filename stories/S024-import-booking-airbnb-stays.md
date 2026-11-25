---
id: S024
title: "Import Booking.com and Airbnb stays"
epic: import
depends_on: [S003, S004, S017]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller who books on Booking.com or Airbnb, **I want** my confirmation e-mail or PDF to become a stay, **so that** I never retype a hotel booking.

## Technical description

- Input: the confirmation saved as `.eml` (or `.mht`/`.html`) or printed to PDF, passed to `kitinerary-extractor` (S003). KItinerary ships extractors for Booking.com and a fix for Airbnb confirmations (seen in its source, 2026-11-24).
- The stay keeps the booking's `url` / `potentialAction` so S017 shows "Manage booking on <site>".
- No login, no scraping, no API: neither site offers a guest API (issue #24).
- Sample confirmations go to the test corpus only once anonymised (no real names, addresses or references in the public repository).

## Acceptance Criteria

### Scenario: A Booking.com confirmation e-mail

* **Given** a Booking.com confirmation saved as `.eml`
* **When** the user imports it
* **Then** the confirmation sheet shows one stay with name, address, check-in and check-out
* **And** the saved stay offers "Manage booking on Booking.com"

### Scenario: An Airbnb confirmation printed to PDF

* **Given** an Airbnb confirmation printed to PDF
* **When** the user imports it
* **Then** a stay is proposed, or the manual stay editor opens pre-filled with what was read

## Notes

- Depends on the findings of issue #24 (which formats KItinerary really reads today).
- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
