---
id: S056
title: "Share my location over Matrix"
epic: comfort
depends_on: [S039]
status: proposed
estimate: L
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller, **I want** to share my position or my next arrival in a Matrix room, **so that** the people waiting for me can follow, on a network I trust.

## Technical description

- KDE Itinerary "added location sharing via Matrix" (23.08) and works on syncing trips over Matrix with end-to-end encryption (blog, 2024–2025).
- Escale: log in to the user's Matrix account (homeserver, SSO or password), pick a room, send a location (`m.location`) or a short arrival message; live location sharing to investigate.
- Library to choose (`matrix-nio`, Apache-2.0, with E2EE via libolm — check its status and Android build). E2EE rooms must work, or the action is refused there.
- Trip sync stays on Nextcloud (ADR-0004); Matrix is for sharing with others.

## Acceptance Criteria

### Scenario: Share the hotel

* **Given** a logged-in Matrix account
* **When** the user shares the stay's location to a room
* **Then** the room receives a location event with the hotel's name

### Scenario: Not logged in

* **Given** no Matrix account is connected
* **When** the user chooses "Share on Matrix"
* **Then** Escale asks to connect an account first

## Notes

- Needs an investigation issue on the Matrix library before `todo`.
- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
