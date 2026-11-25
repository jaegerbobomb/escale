---
id: S043
title: "Local transfers between places"
epic: live
depends_on: [S039, S040]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** to see how to get from home to the station and from the station to the hotel, **so that** the whole door-to-door journey is in the timeline.

## Technical description

- KDE Itinerary: "local ground transportation navigation between elements of your itinerary" and favourite locations. Escale: home and favourite places in the preferences; transfer cards before the first and after the last segment, and between segments in different places.
- Journey from Transitous; can start from the current location (KDE 2025).

## Acceptance Criteria

### Scenario: To the station

* **Given** a home location and a train at 10:12 from Paris Gare de Lyon
* **Then** a transfer card before the train proposes a connection from home

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
