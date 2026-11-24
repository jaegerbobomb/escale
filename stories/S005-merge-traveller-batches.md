---
id: S005
title: "Merge reservations into traveller batches"
epic: import
depends_on: [S003]
status: proposed
estimate: M
bdd: true
updated: "2026-11-24"
---

## User story

> **As a** traveller booking for several people, **I want** one entry per train or
> hotel with everyone on it, **so that** re-importing or importing each ticket does not
> clutter my trip.

## Technical description

- Core domain `merge`: a simplified port of KItinerary's `MergeUtil` rules.
  - *same reservation*: same type, same reservation number or same traveller, same
    incidence → merge (newer non-empty fields win, raw JSON-LD of both kept until saved);
  - *same incidence*: same type and same trip (train number + departure date and
    station, or hotel + check-in date) but another traveller → add to the batch;
  - otherwise a new batch.
- A batch is one calendar event later (S007).
- Unit tests per rule, with JSON-LD fixtures.

## Acceptance Criteria

### Scenario: The same ticket imported twice

* **Given** a saved train reservation for Alix on TGV 9339 on 8 July
* **When** the same ticket is imported again
* **Then** there is still one reservation for Alix on that train

### Scenario: A second traveller joins the batch

* **Given** a saved train reservation for Alix on TGV 9339 on 8 July
* **When** a ticket for Léa on TGV 9339 on 8 July is imported
* **Then** the batch for that train holds two travellers

### Scenario: Another train is another batch

* **Given** a saved train reservation for Alix on TGV 9339 on 8 July
* **When** a ticket for Alix on IC 9264 on 8 July is imported
* **Then** there are two batches

## Notes

- KItinerary's exact rules live in its C++ `MergeUtil`; this port is deliberately
  smaller. Cases it gets wrong are fixed by completing this story (bug doctrine).
