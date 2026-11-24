---
id: S010c
title: "Segment card densities"
epic: timeline
depends_on: [S010b]
status: proposed
estimate: S
bdd: true
updated: "2026-11-24"
adr: [7]
---

## User story

> **As a** traveller, **I want** cards that show more or less depending on where I am,
> **so that** a disruption stands out and lists stay compact.

## Technical description

- One card component, three densities (mockup "Carte-segment — 3 densités"): compact
  (lists), detailed (timeline, S010b), disruption (cancellation in focus, recovery
  action visible without a click).

## Acceptance Criteria

### Scenario: A cancelled train uses the disruption card

* **Given** a current trip with a cancelled train
* **When** the "Current" tab is shown
* **Then** that train's card shows the cancellation and a "See alternatives" action

## Notes

- Child of S010 (split validated by the maintainer, 2026-11-24). Cancellations come
  from real-time data (`live` epic); until then only from the ticket's own status.
