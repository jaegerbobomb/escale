---
id: S011
title: "Jump index and segment detail"
epic: timeline
depends_on: [S010]
status: proposed
estimate: M
bdd: true
updated: "2026-11-24"
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
