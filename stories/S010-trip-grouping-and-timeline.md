---
id: S010
title: "Trip grouping and timeline"
epic: timeline
depends_on: [S002, S014]
status: todo
estimate: L
bdd: true
updated: "2026-11-24"
adr: [7]
---

## User story

> **As a** traveller, **I want** my bookings grouped into trips and shown as a timeline,
> **so that** I see my journey in order at a glance.

## Technical description

- Core domain `grouping`: reservations close in time and forming a journey away from
  home and back become one trip; same-day local events with no overnight stay become
  an outing. A named or forced grouping (`X-ESCALE-TRIP`) always wins.
- "Current" shows the active trip (the one in progress, else the next one): header
  with name, dates, travellers; stacked timeline of segment cards (detailed density),
  country-change rows between segments, the next segment highlighted.
- Card densities as one component: compact, detailed, disruption.
- Split into sub-stories if needed (grouping / timeline view / card densities).

## Acceptance Criteria

### Scenario: A return trip becomes one trip

* **Given** a train from Paris to London on 8 July, a hotel in London from 8 to 10 July, and a train back on 10 July
* **When** the reservations are grouped
* **Then** they form one trip named "London"

### Scenario: A dinner and a concert become an outing

* **Given** a restaurant booking at 19:30 and a concert ticket at 21:00 in Paris on the same evening
* **When** the reservations are grouped
* **Then** they form one outing

### Scenario: The next segment is highlighted

* **Given** a current trip whose first train leaves in 40 minutes
* **When** the "Current" tab is shown
* **Then** that train's card is highlighted as next

### Scenario: A cancelled train uses the disruption card

* **Given** a current trip with a cancelled train
* **When** the "Current" tab is shown
* **Then** that train's card shows the cancellation and a "See alternatives" action
