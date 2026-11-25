---
id: S052
title: "Export an .itinerary file"
epic: comfort
depends_on: [S028]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** user, **I want** to export a trip or everything as an `.itinerary` file, **so that** I can back up, or open it in KDE Itinerary.

## Technical description

- Same zip layout as S028; written so KDE Itinerary imports it (test with KDE Itinerary in CI if feasible, else by hand).

## Acceptance Criteria

### Scenario: Round trip

* **Given** a trip exported by Escale
* **When** it is imported in KDE Itinerary
* **Then** the same reservations and documents appear

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
