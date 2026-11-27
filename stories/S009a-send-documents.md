---
id: S009a
title: "Send ticket documents to Nextcloud"
epic: sync
depends_on: [S008c]
status: done
estimate: S
bdd: true
updated: "2026-11-27"
adr: [4]
released_in: "0.23.0"
---

## User story

> **As a** traveller who imports a ticket on my laptop, **I want** its PDF kept in my
> Nextcloud with the reservation, **so that** my other devices can get it.

## Technical description

- Child of S009. Each sync run, between receiving and sending events, uploads the
  documents that have a local file and are not on the server yet, as
  `Escale/documents/<sha256>/<file name>` then `meta.json` (schema.org
  `DigitalDocument`: `name`, `encodingFormat`; SPEC § Documents). `meta.json` is written
  last: when it is there, the document is complete.
- A document is immutable: when `meta.json` is already on the server, nothing is
  uploaded; a file is created, never overwritten (`If-None-Match: *`).
- Events carry the document ids in each reservation's schema.org `subjectOf`, as
  KItinerary's `DocumentUtil` does; reading an event takes them back into the
  reservation. A reservation whose documents changed is sent again, so events written
  before this story get their `subjectOf` on the next run.
- The store remembers which documents were uploaded (SQLite schema 4).
- An unreachable server stops the run before any event is written: an event never points
  to a document the server does not have, as far as this device knows.

## Acceptance Criteria

### Scenario: A ticket's PDF goes to the server with its reservation

* **Given** a device connected to a calendar
* **When** a ticket is imported with its PDF
* **And** the device syncs
* **Then** the server has the PDF and its meta.json in the document's folder
* **And** the calendar event names that document in subjectOf

### Scenario: The same document is not uploaded twice

* **Given** a PDF already present on the server
* **When** the same PDF is imported again on another device
* **And** that device syncs
* **Then** no file is uploaded

### Scenario: A reservation received from another device keeps its documents

* **Given** two devices connected to the same calendar
* **When** a ticket is imported with its PDF on the first device
* **And** both devices sync
* **Then** the second device's reservation names that document

## Notes

- 2026-11-27: split of S009 validated by the maintainer.
- 2026-11-27: Nextcloud 31 answers `404` to a `PUT` into a missing folder (not `409`),
  `405` to a `MKCOL` of an existing one, `412` to `If-None-Match: *` on an existing file
  (checked on a local Nextcloud 31). `caldav` turns the line ends of a body into CRLF
  unless it is `WireBytes`: without it a PDF arrives corrupted (red → green on the real
  server, `test_put_file_makes_its_folders_and_never_overwrites`).
- The `meta.json` written is `{"@type": "DigitalDocument", "name", "encodingFormat"}`,
  as the local store wrote it since S014; that it matches KDE Itinerary's own
  `meta.json` field for field is not checked against its source (not verified).
