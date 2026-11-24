---
id: S009
title: "Sync ticket documents"
epic: sync
depends_on: [S006, S003]
status: todo
estimate: M
bdd: true
updated: "2026-11-24"
adr: [4]
---

## User story

> **As a** traveller on my phone, **I want** the PDF and passes of my tickets, **so that**
> I can show them at the gate even offline.

## Technical description

- Core service `documents`: upload a new document to `Escale/documents/<sha256>/`
  (`meta.json` + file) before its event is written; passes to
  `Escale/passes/<passTypeId>/<serial>.pkpass` (`SPEC.md` § Documents).
- Download on demand when a document is opened; prefetch all documents of the current
  trip in the background, so they are available offline.
- A document is immutable: upload only what is missing, never overwrite.
- Local cache with a size limit; documents of past trips can be evicted.

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

### Scenario: The same document is not uploaded twice

* **Given** a PDF already present on the server
* **When** the same PDF is imported again
* **Then** no file is uploaded

## Notes

- 2026-11-24: validated by the maintainer (`todo`).
