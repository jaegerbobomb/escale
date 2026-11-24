---
id: S003
title: "Extract a ticket with kitinerary"
epic: import
depends_on: [S001]
status: done
estimate: M
bdd: true
updated: "2026-11-24"
released_in: "0.3.0"
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

* **Given** a train ticket that kitinerary-extractor understands
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

* **Given** a train ticket that kitinerary-extractor understands
* **When** the file is extracted
* **Then** the reservation's subjectOf contains the SHA-256 of the file

## Notes

- 2026-11-24: validated by the maintainer (`proposed` → `todo`), delivered in 0.3.0.
- **Sample files** (maintainer's choice): kitinerary reads a PDF train ticket only through
  an operator-specific extractor, and no synthetic one exists that would not imitate a
  real operator's ticket. So the scenarios say "a train ticket" instead of "a PDF train
  ticket"; they run the service with a fake extractor that returns what the real binary
  printed for `tests/data/train-booking.html` (schema.org JSON-LD). The real binary is
  tested on that HTML ticket, on KDE's CC0 boarding pass PDF (`iata-bcbp-demo.pdf`) and
  on a PDF with no reservation.
- **Binary resolution**: `PATH`, then the configured path, then the distribution paths
  (`/usr/lib/<arch>/libexec/kf5|kf6`, `/usr/libexec/kf5|kf6`): Debian and Ubuntu install
  it there, outside `PATH`. The configured path is a parameter of the adapter; no
  setting exposes it yet. Shipping the static binary stays in issue #5.
- CI installs `libkpim5itinerary5` on an `ubuntu-24.04` runner (kitinerary 23.08; the
  package is gone from 26.04, which `ubuntu-latest` now is) and runs the
  adapter tests with `ESCALE_REQUIRE_KITINERARY=1`, so a missing binary fails them.
- kitinerary prints date-times either as strings or as `{"@type": "QDateTime",
  "@value": …, "timezone": …}` objects; both are read.
- The document id is the SHA-256 of the file; it is attached through
  `ExtractedReservation.subject_of`, and the raw JSON-LD is kept as printed.

