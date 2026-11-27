---
id: S008c
title: "A conflicting edit keeps the server version"
epic: sync
depends_on: [S008b]
status: todo
estimate: S
bdd: true
updated: "2026-11-27"
adr: [4]
---

## User story

> **As a** traveller who edited a booking on two devices, **I want** one clear outcome
> and to be told about it, **so that** I do not lose track of which version is kept.

## Technical description

- Child of S008. When a `PUT` gets `412 Precondition Failed`, or the pull finds a
  reservation changed on the server while it has an entry in the outbox: the server
  version wins (v1, ADR-0004), the outbox entry is dropped, the local store takes the
  server's event.
- The UI says so once, as a toast: "<title> was changed on another device; that
  version is kept."
- No merge of fields and no choice offered in v1.

## Acceptance Criteria

### Scenario: A conflicting edit keeps the server version

* **Given** a reservation edited on the server since the device last synced
* **When** the device sends its own edit of that reservation
* **Then** the device shows the server version
* **And** the user is told the reservation changed elsewhere

## Notes

- Split from S008 (2026-11-27), validated by the maintainer (`todo`).
