---
id: S033
title: "Create an outing by hand"
epic: outings
depends_on: [S032]
status: proposed
estimate: S
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** user, **I want** to create an outing before I have any ticket, **so that** I can plan an evening and add bookings as they come.

## Technical description

- "Add → New outing": name, date. Bookings added later can be attached to it.
- A hand-made outing is never regrouped automatically (`X-ESCALE-TRIP`).

## Acceptance Criteria

### Scenario: Empty outing

* **Given** no outing on 12 March
* **When** the user creates "Birthday" on 12 March
* **Then** "My trips" lists an empty outing "Birthday" on 12 March

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
