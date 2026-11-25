---
id: S060
title: "iOS build"
epic: packaging
depends_on: [S058]
status: proposed
estimate: L
bdd: false
updated: "2026-11-25"
---

## User story

> **As a** iPhone user, **I want** Escale on iOS, **so that** my trips are on my phone whatever it is.

## Technical description

- v2. macOS runner, Apple developer account, pure-Python or iOS-wheel dependencies, pkpass handed to Apple Wallet; licence through `COPYING.iOS`.

## Acceptance Criteria

### Scenario: TestFlight build

* **Given** the iOS signing secrets are set
* **When** CI builds a version tag
* **Then** an iOS build is uploaded to TestFlight

## Notes

- v2, see the roadmap.
- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
