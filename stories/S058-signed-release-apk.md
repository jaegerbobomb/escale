---
id: S058
title: "Signed release APK from a tag"
epic: packaging
depends_on: [S013]
status: proposed
estimate: S
bdd: false
updated: "2026-11-25"
---

## User story

> **As a** maintainer, **I want** CI to build a signed APK when I push a version tag, **so that** releases are reproducible and the key never sits in the repository.

## Technical description

- GitHub Actions on `v*` tags: `flet build apk --release`, signed with a key from the repository secrets, attached to the GitHub release.
- F-Droid later (reproducible build to check).

## Acceptance Criteria

### Scenario: Tag v0.20.0

* **Given** the signing key is in the repository secrets
* **When** the maintainer pushes the tag `v0.20.0`
* **Then** the release v0.20.0 holds a signed APK

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
