---
id: S012
title: "Train segment editor"
epic: timeline
depends_on: [S011, S008]
status: proposed
estimate: M
bdd: true
updated: "2026-11-24"
---

## User story

> **As a** traveller, **I want** to correct a train booking that was read wrongly, **so
> that** my timeline is right without re-importing.

## Technical description

- In the segment detail, "Edit" shows exactly KDE Itinerary's `TrainEditor` fields:
  train name/number; departure station, time, platform; arrival station, time,
  platform; coach, seat, class.
- Real-time data (delay, live platform, weather, occupancy) stays read-only, with a
  notice saying it is fetched automatically.
- "Save" updates the raw JSON-LD and the event (through the sync outbox); "Cancel"
  discards.

## Acceptance Criteria

### Scenario: Correcting a seat

* **Given** the detail of a train with coach 12 seat 41
* **When** the user edits the seat to 48 and saves
* **Then** the detail shows coach 12 seat 48
* **And** the change is queued for sync

### Scenario: Cancelling an edit

* **Given** the detail of a train with coach 12 seat 41
* **When** the user edits the seat to 48 and cancels
* **Then** the detail shows coach 12 seat 41

### Scenario: Real-time fields are not editable

* **Given** the detail of a train with a delay of 12 minutes
* **When** the user opens the editor
* **Then** the delay is not an editable field
