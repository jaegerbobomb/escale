---
id: S025b
title: "Share a ticket to Escale on Android"
epic: import
depends_on: [S025a, S058]
status: proposed
estimate: M
bdd: true
updated: "2026-11-28"
adr: [9]
---

## User story

> **As a** traveller on my phone, **I want** to share a ticket from my mail app to
> Escale, **so that** it reaches my trips without a computer at hand.

## Technical description

- Child of S025. Escale's own Flet extension `escale-share` (ADR-0009) wraps
  `receive_sharing_intent`; intent filters for PDF, pkpass, `.eml`, images and text in
  `[tool.flet.android.activity]`.
- Android has no extractor in v1 (ADR-0003): a shared file goes to an "Inbox" and is
  imported by the Linux app at the next sync; the user is told so. An `.itinerary`
  file is read on the phone itself (S028).
- First, a prototype APK checks that a share reaches Python with Escale closed and
  open (ADR-0009).

## Acceptance Criteria

### Scenario: Share a ticket on Android

* **Given** a ticket PDF in a mail app on Android
* **When** the user shares it to Escale
* **Then** the file is listed in the Inbox as "waiting for import on Linux"

## Notes

- 2026-11-28: split of S025 approved by the maintainer; waits for S058's APK builds.
