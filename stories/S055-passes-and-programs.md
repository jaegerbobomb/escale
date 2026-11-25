---
id: S055
title: "Discount cards and passes"
epic: comfort
depends_on: [S015]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller with a rail card, **I want** my discount cards and passes in one place, **so that** I show them at a ticket check without searching.

## Technical description

- A "Passes & programs" page (KDE Itinerary has one; to check its exact scope): schema.org `ProgramMembership` (rail cards, loyalty programs) and non-trip pkpass.
- Validity dates; expired ones greyed with the date.

## Acceptance Criteria

### Scenario: Rail card

* **Given** an imported rail card valid until 2027
* **Then** the page lists it with its barcode and expiry date

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
