---
id: S041
title: "Notify changes"
epic: live
depends_on: [S040]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** a notification when my train changes, **so that** I do not have to watch the app.

## Technical description

- Local notifications (Flet 1.1) for delay over a threshold, platform change, cancellation; one per change, grouped per segment.
- Android: no push service; only while the app or a foreground service runs (to investigate). Linux: desktop notification.

## Acceptance Criteria

### Scenario: Platform change

* **Given** a tracked train on platform 7
* **When** the platform becomes 9
* **Then** a notification says "Platform now 9"

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
