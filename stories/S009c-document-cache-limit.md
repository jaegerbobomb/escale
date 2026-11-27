---
id: S009c
title: "Limit the space taken by ticket documents"
epic: sync
depends_on: [S009b]
status: todo
estimate: S
bdd: true
updated: "2026-11-27"
adr: [4]
---

## User story

> **As a** traveller with a small phone, **I want** old ticket documents to stop taking
> space, **so that** Escale does not fill my storage.

## Technical description

- Child of S009. A size limit for the local documents (default to decide: to ask the
  maintainer before coding).
- Over the limit, documents of past trips are removed from the device, oldest trip
  first; they stay on the server and download again when opened (S009b).
- Documents of current and future trips, and documents not on the server yet, are never
  removed.

## Acceptance Criteria

### Scenario: Documents of past trips are removed over the limit

* **Given** a device over its document limit with a past trip and a future trip
* **When** the device cleans its documents
* **Then** the past trip's documents are removed from the device
* **And** the future trip's documents are kept

### Scenario: A removed document comes back when opened

* **Given** a past trip whose document was removed from the device
* **When** the user opens that document with network
* **Then** the document is shown

## Notes

- 2026-11-27: split of S009 validated by the maintainer.
