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

- In the header bar, on every tab, a "Ticket" button when the active trip's next
  segment (the one outlined, S010b) has a ticket: a barcode or a kept document (S015).
  Wide window: "Ticket" button left of "Add"; narrow: a ticket icon next to "+".
- It opens that segment's ticket full screen, as "Ticket" on its card does.
- No next segment with a ticket: no button.

## Acceptance Criteria

### Scenario: The button opens the next segment's ticket

* **Given** a current trip whose next train has a ticket
* **When** the user presses "Ticket" in the header bar
* **Then** that train's ticket is shown full screen

### Scenario: The button is there on every tab

* **Given** a current trip whose next train has a ticket
* **When** the "My trips" tab is shown
* **Then** the header bar has the "Ticket" button

### Scenario: No ticket, no button

* **Given** a current trip whose next segment has no ticket
* **When** the "Current" tab is shown
* **Then** the header bar has no "Ticket" button

## Notes

- Asked by the maintainer when validating S015 (2026-11-24); validated on that request.
- First placed in the trip header; moved to the header bar at the maintainer's request
  (2026-11-24), so that it is reachable from every tab. A dedicated "Ticket(s)" tab was
  mentioned as an option, not decided (the mockup's mobile bar once had "Tickets").
