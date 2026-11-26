---
id: S025
title: "Share a file to Escale"
epic: import
depends_on: [S003, S004]
status: todo
estimate: M
bdd: true
updated: "2026-11-26"
---

## User story

> **As a** traveller, **I want** to send a ticket to Escale from my mail or file app, **so that** importing is one gesture, as in KDE Itinerary.

## Technical description

- **Android**: Escale registers as a share target for PDF, pkpass, `.eml`, images and text (links). Flet support for share intents is investigated in issue #19.
- **Linux**: a `.desktop` entry with the MIME types, so "Open with Escale" works from Files and mail clients; the file goes to the import flow (S004).
- On Android, which has no extractor in v1 (ADR-0003), a shared file is kept in an "Inbox" and imported by the Linux app at the next sync; the user is told so.
- Shared text that is a link goes to the place import (S019) when it is a map link.

## Acceptance Criteria

### Scenario: Open a PDF with Escale on Linux

* **Given** a ticket PDF in the Files app
* **When** the user chooses "Open with Escale"
* **Then** Escale shows the import confirmation for that file

### Scenario: Share a ticket on Android

* **Given** a ticket PDF in a mail app on Android
* **When** the user shares it to Escale
* **Then** the file is listed in the Inbox as "waiting for import on Linux"

## Notes

- Blocked by issue #19 for Android.
- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
- 2026-11-26: validated by the maintainer (`todo`), to follow the sync arc (S006–S009).
