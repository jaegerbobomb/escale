---
id: S021
title: "Shortcut to the current ticket"
epic: timeline
depends_on: [S015, S010b]
status: done
estimate: S
bdd: true
updated: "2026-11-24"
released_in: "0.9.0"
---

## User story

> **As a** traveller at the gate or on board, **I want** one button that opens the ticket
> I need now, **so that** I do not scroll the timeline to find it.

## Technical description

- In "Current", the trip header has a "Show ticket" button when the next segment (the
  one outlined, S010b) has a ticket: a barcode or a kept document (S015).
- It opens that segment's ticket full screen, as "Ticket" on its card does.
- No next segment with a ticket: no button.

## Acceptance Criteria

### Scenario: The button opens the next segment's ticket

* **Given** a current trip whose next train has a ticket
* **When** the user presses "Show ticket"
* **Then** that train's ticket is shown full screen

### Scenario: No ticket, no button

* **Given** a current trip whose next segment has no ticket
* **When** the "Current" tab is shown
* **Then** there is no "Show ticket" button

## Notes

- Asked by the maintainer when validating S015 (2026-11-24); validated on that request.
- Delivered in 0.9.0: "Show ticket" (filled button) at the right of the trip header.
  Its place may move with S020 (the mockup's header).
