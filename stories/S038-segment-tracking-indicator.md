---
id: S038
title: "Show whether a segment is tracked"
epic: live
depends_on: [S010b, S039]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** to see on each segment whether it is followed live, and why not, **so that** a grey button never leaves me guessing.

## Technical description

- Per segment: "Live" when a source covers it (Transitous for trains and buses), else "Not tracked" with the reason (flight in v1, line not covered, source off, offline).
- "Refresh" refreshes tracked segments and updatable passes; disabled with its reason when there is nothing to refresh (agreed 2026-11-24).

## Acceptance Criteria

### Scenario: An imported flight

* **Given** a flight segment
* **Then** it shows "Not tracked: flights are not followed yet"

### Scenario: Nothing to refresh

* **Given** a trip with only a flight and a hotel
* **Then** "Refresh" is disabled and says why

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
