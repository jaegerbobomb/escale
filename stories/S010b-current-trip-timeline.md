---
id: S010b
title: "Current trip timeline"
epic: timeline
depends_on: [S010a, S002]
status: todo
estimate: M
bdd: true
updated: "2026-11-24"
adr: [7]
---

## User story

> **As a** traveller, **I want** the "Current" tab to show my trip as a timeline, **so
> that** I see my journey in order at a glance.

## Technical description

- "Current" shows the active trip (S010a): header with name, dates, travellers; stacked
  timeline of segment cards in the "detailed" density (mockup "Voyage en cours"); the
  next segment highlighted.
- No active trip: the empty view of S002 stays.
- Screenshot routes in demo mode, as in S004.

## Acceptance Criteria

### Scenario: The current trip is shown in order

* **Given** a stored trip to London with a train, a hotel and a train back
* **When** the "Current" tab is shown
* **Then** the three segments are shown in time order under the trip's name

### Scenario: The next segment is highlighted

* **Given** a current trip whose first train leaves in 40 minutes
* **When** the "Current" tab is shown
* **Then** that train's card is highlighted as next

## Notes

- Child of S010 (split validated by the maintainer, 2026-11-24).
