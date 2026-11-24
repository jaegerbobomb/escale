---
id: S015
title: "Full-screen ticket, offline"
epic: timeline
depends_on: [S014]
status: todo
estimate: M
bdd: true
updated: "2026-11-24"
adr: [3]
---

## User story

> **As a** traveller at a gate or on a train, **I want** to show my ticket full screen
> with its barcode, without network, **so that** an inspector or a gate can scan it.

## Technical description

- From a reservation, "Ticket" opens a full-screen view (mockup "Import PDF & offline
  ticket", step 3): train or flight number, route, date and time, coach and seat, the
  barcode as large as the width allows, its number below it.
- Barcode from the reservation's `reservedTicket.ticketToken` as kitinerary prints it
  (`qrCode:`, `aztecCode:`, `aztecbin:`, `pdf417:`, `barcode128:`, `dataMatrix:` …),
  drawn locally (GPL-compatible Python libraries, to choose in this story); no network.
- Several travellers on one booking: one page per traveller, swiped (like
  `AdwCarousel`).
- No barcode: the view offers the original document (the PDF stored by S014).
- Screen brightness at maximum while the view is open, if Flet allows it on the
  platform; otherwise a note in the story.
- Screenshot routes for the view (demo mode, as in S004).

## Acceptance Criteria

### Scenario: A ticket with a QR code

* **Given** a stored train reservation whose ticket token is a QR code
* **When** the user opens its ticket
* **Then** the QR code is shown and encodes the ticket token's content
* **And** the train number, route, date, coach and seat are shown

### Scenario: Works offline

* **Given** a stored reservation with a ticket token
* **When** the user opens its ticket with no network
* **Then** the barcode is shown

### Scenario: No barcode

* **Given** a stored reservation without ticket token but with its PDF
* **When** the user opens its ticket
* **Then** the view offers to open the PDF

## Notes

- Asked by the maintainer (2026-11-24): showing tickets and trips comes first, close to
  KDE Itinerary on Android. Validated (`todo`) on that request.
