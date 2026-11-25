---
id: S048
title: "Coach layout and platform section"
epic: stations
depends_on: [S040]
status: proposed
estimate: L
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** train traveller with a seat, **I want** to know where my coach stops on the platform, **so that** I wait at the right place.

## Technical description

- KDE Itinerary shows a coach layout "for some operators only" and uses it with the seat to highlight the departure spot on the platform.
- Source: operators' formation data (DB, ÖBB, SNCF…); Transitous does not provide it (to check). Per-operator adapter, opt-in.

## Acceptance Criteria

### Scenario: Coach 12

* **Given** a reservation in coach 12 and a known formation
* **Then** the segment detail shows coach 12 in section C of the platform

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
