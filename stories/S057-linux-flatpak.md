---
id: S057
title: "Linux package with the extractor"
epic: packaging
depends_on: [S003]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** Linux user, **I want** to install Escale in one step, **so that** I do not build anything.

## Technical description

- Flatpak (GNOME's recommended distribution, Flathub) with the static `kitinerary-extractor` inside.
- Sandbox: portals for files, camera, notifications.

## Acceptance Criteria

### Scenario: Clean install

* **Given** a fresh system with Flatpak
* **When** the user installs the Escale Flatpak
* **Then** importing a ticket works without anything else installed

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
