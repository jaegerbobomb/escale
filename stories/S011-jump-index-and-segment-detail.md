---
id: S011
title: "Jump index and segment detail"
epic: timeline
depends_on: [S010]
status: done
estimate: M
bdd: true
updated: "2026-11-24"
released_in: "0.11.0"
adr: [7]
---

## User story

> **As a** traveller, **I want** to jump to a part of my trip and open a segment's
> details, **so that** I find my seat or platform fast and come back where I was.

## Technical description

- Wide window (≥ 550 px): jump index panel on the left; a click scrolls the timeline
  and highlights the card, without changing the view.
- 400–550 px: "Jump to…" menu; < 400 px: bottom sheet.
- Clicking a card replaces the content with the segment detail and a "‹ <trip>"
  button; < 400 px it is a pushed page and the bottom bar hides.
- "‹ <trip>" restores the scroll position and highlights the card.

## Acceptance Criteria

### Scenario: The index scrolls without leaving the timeline

* **Given** a trip with five segments is open in a window 1000 px wide
* **When** the user clicks "Tate Modern" in the jump index
* **Then** the timeline scrolls to the Tate Modern card and highlights it
* **And** the timeline is still shown

### Scenario: Back returns to the same place

* **Given** a trip is open and scrolled to its return train
* **When** the user opens the return train's detail
* **And** goes back to the trip
* **Then** the timeline is scrolled to the return train card
* **And** that card is highlighted

### Scenario: The index becomes a menu on a medium window

* **Given** a trip is open in a window 500 px wide
* **Then** the jump index panel is not shown
* **And** a "Jump to…" action is available

### Scenario: The detail is a pushed page on a narrow window

* **Given** a trip is open in a window 380 px wide
* **When** the user opens a segment's detail
* **Then** the bottom navigation bar is hidden

## Notes

- 2026-11-24: validated by the maintainer (`todo`).
- Delivered in 0.11.0. Wide: a 240 px "Jump to" panel left of the timeline; medium: a
  "Jump to…" menu in the trip header; narrow (< 400 px): a button opening a bottom
  sheet. Jumping scrolls (`scroll_to(scroll_key=…)`) and tints the card.
- The timeline is a scrolling `Column`, not a `ListView`: Flet's `scroll_to` with a key
  does nothing on lazily built lists (Flet 1.1.3 docs). Checked in a browser: the
  `/trip-jump` demo route lands on the Tate Modern card.
- Detail: title, departure/arrival (time, station, platform), seat, place or address,
  travellers, booking reference, "Ticket"; "‹ <trip>" goes back, scrolled to the card
  and with it highlighted. Read-only; editing is S012 (train) and S017 (stay).
- The demo trip has five segments (`LONDON_TRIP_FULL`: museum and dinner added).
- 2026-11-25, when validating S016: the maintainer is not fond of the layout of the
  detail's action buttons (row under the title). To revisit later, not blocking.
