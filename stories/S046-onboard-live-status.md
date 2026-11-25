---
id: S046
title: "Live status on board"
epic: live
depends_on: [S039]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** train passenger on board, **I want** to see where the train is and its next stops, **so that** I know my arrival while on the train Wi-Fi.

## Technical description

- KDE Itinerary reads onboard APIs of some trains and coaches (ICE, ÖBB Railjet, Eurostar, Flixbus… — list in KPublicTransport, to check). Escale: detect the on-board network, read the same API, show speed, position and next stops.
- Only when connected to the operator's Wi-Fi; no request otherwise.

## Acceptance Criteria

### Scenario: On an ICE

* **Given** the device is on the ICE on-board Wi-Fi
* **Then** the current segment shows the next stop and its expected time

## Notes

- Per-operator adapters; start with the ones the maintainer travels with.
- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
