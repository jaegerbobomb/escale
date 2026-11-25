---
id: S034
title: "Walks and the last ride home"
epic: outings
depends_on: [S032, S043]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** user on an evening out, **I want** to see how to go from one place to the next and the last metro home, **so that** I do not miss the end of the evening.

## Technical description

- Between two places of an outing: a transfer card (walk or local transport) from the local transfers (S043).
- After the last event: "Last ride home" to the home location, from Transitous; hidden when the home location is not set or the source is off.

## Acceptance Criteria

### Scenario: Last metro

* **Given** an outing ending at 23:30 and a home location
* **When** Transitous returns a last connection at 00:41
* **Then** the outing ends with "Last ride home 00:41"

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
