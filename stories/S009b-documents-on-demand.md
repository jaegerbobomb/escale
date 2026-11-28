---
id: S009b
title: "Ticket documents on every device"
epic: sync
depends_on: [S009a]
status: done
estimate: S
bdd: true
updated: "2026-11-27"
adr: [4]
released_in: "0.24.0"
---

## User story

> **As a** traveller on my phone, **I want** the PDF of a ticket imported on my laptop,
> **so that** I can show it at the gate even offline.

## Technical description

- Child of S009. Opening a document that is not on the device downloads it from
  `Escale/documents/<sha256>/` (`meta.json` gives the file name), keeps it in the local
  layout (`documents/<sha256>/`) and opens it.
- After each sync run, the documents of the current trip that are missing locally are
  downloaded in the background.
- A document whose content does not match its id is not kept.
- No network: the document says it is not on this device yet.

## Acceptance Criteria

### Scenario: A document imported on Linux opens on Android

* **Given** a ticket imported on Linux with its PDF
* **When** the user opens that ticket on Android
* **Then** the PDF is shown

### Scenario: Documents of the current trip work offline

* **Given** a current trip with two ticket PDFs on the server
* **And** the device has synced once
* **When** the device goes offline
* **Then** both PDFs open

## Notes

- 2026-11-27: split of S009 validated by the maintainer.
- "Current trip" is the one in progress, else the next to start (`active_trip`, S010a).
- Without a connected account, a document not on the device offers no "Booking
  document" action, as before: there is nothing to download it from.
- Downloads bypass `caldav`, whose responses turn CRLF into LF (that breaks a PDF):
  checked on Nextcloud 31 by `test_get_file_returns_the_bytes_unchanged`.
- Toast wording to validate on the screenshots: "This document is not on this device
  yet. It downloads when the server can be reached."
