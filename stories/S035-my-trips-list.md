---
id: S035
title: "My trips list"
epic: browse
depends_on: [S010a]
status: done
estimate: M
bdd: true
updated: "2026-11-28"
released_in: "0.26.0"
---

## User story

> **As a** traveller, **I want** a list of my upcoming and past trips and outings, **so that** I find any trip in seconds.

## Technical description

- "My trips" tab: upcoming first, then past by year; filter All / Trips / Outings; text search on names, places and references. Same two-level view as KDE Itinerary since 24.x (trip list, then the trip's timeline).
- Compact card density (S010c).

## Acceptance Criteria

### Scenario: Filter outings

* **Given** two trips and one outing
* **When** the user chooses "Outings"
* **Then** only the outing is listed

### Scenario: Search a reference

* **Given** a trip holding the booking reference "QX7RTB"
* **When** the user searches "QX7RTB"
* **Then** the trip holding it is listed

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
- 2026-11-26: validated by the maintainer (`todo`), to follow the sync arc (S006–S009).
- 2026-11-28: done in one PR of about 430 lines of production code (list view, pushed
  trip page in the shell, demo data), over the 300-line guideline; the maintainer chose
  one PR over a split. Screenshots validated by the maintainer.
- "Past by year": one section per year of the trip's start, most recent first, after
  "Upcoming" (in progress or to come).
- The search looks in the trip's name and in every text of its reservations' JSON-LD
  (names, places, addresses, references), case ignored.
- Outings' purple is the theme's tertiary container (`#9141ac` light, `#dc8add` dark).
- No per-card menu ("⋯" in the mockup) yet: nothing to put in it in v1.
