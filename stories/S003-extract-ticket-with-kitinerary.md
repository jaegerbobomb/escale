---
id: S003
title: "Extract a ticket with kitinerary"
epic: import
depends_on: [S001]
status: proposed
estimate: M
bdd: true
updated: "2026-11-24"
adr: [3]
---

## User story

> **As a** traveller on Linux, **I want** Escale to read my ticket files, **so that** I
> do not type my bookings by hand.

## Technical description

- Core adapter `kitinerary_cli`: runs `kitinerary-extractor` on a file as a subprocess
  (async), with a timeout, and parses the JSON-LD array it prints.
- Binary resolution: `kitinerary-extractor` on `PATH` if present, else the binary
  shipped with the Linux package (path from configuration). Missing binary is an
  explicit error, not a crash.
- Service `importer.extract(path) -> list[ExtractedReservation]`: keeps the raw JSON-LD
  of each element, maps the fields of the domain model, and attaches the document
  (SHA-256 id, name, MIME type) through `subjectOf`.
- Fake adapter for service tests; adapter tests run the real binary in CI with sample
  files (KDE's synthetic samples where licences allow, or our own).

## Acceptance Criteria

### Scenario: A supported train ticket is extracted

* **Given** a PDF train ticket that kitinerary-extractor understands
* **When** the file is extracted
* **Then** one train reservation is returned with departure and arrival stations and times
* **And** its raw JSON-LD is kept unchanged

### Scenario: A file with nothing recognised

* **Given** a PDF that contains no reservation
* **When** the file is extracted
* **Then** no reservation is returned
* **And** the result says that nothing was recognised

### Scenario: The extractor is missing

* **Given** no kitinerary-extractor is available
* **When** a file is extracted
* **Then** the result is an error saying the extractor is not installed

### Scenario: The document is linked to its reservation

* **Given** a PDF train ticket that kitinerary-extractor understands
* **When** the file is extracted
* **Then** the reservation's subjectOf contains the SHA-256 of the file
