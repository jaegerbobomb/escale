---
id: S015
title: "Full-screen ticket, offline"
epic: timeline
depends_on: [S014]
status: done
estimate: M
bdd: true
updated: "2026-11-25"
released_in: "0.8.0"
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

### Scenario: A hotel booking is not a ticket

* **Given** a stored hotel booking without ticket token but with its PDF
* **When** the current trip is shown
* **Then** the booking's card has no "Ticket" button
* **And** its detail offers to open the booking document

## Notes

- Asked by the maintainer (2026-11-24): showing tickets and trips comes first, close to
  KDE Itinerary on Android. Validated (`todo`) on that request.
- Delivered in 0.8.0. Token prefixes from KItinerary 23.08 (`datatypes/token.cpp`):
  `qrcode:`, `qrcodebin:`, `azteccode:`, `aztecbin:`, `pdf417:`, `pdf417bin:`,
  `barcode128:`, `datamatrix:` (case-insensitive, `bin` = base64).
- Drawn locally to PNG: QR (`segno`, BSD), Aztec (`aztec-code-generator`, MIT), PDF417
  (`pdf417gen`, MIT), Code 128 (`python-barcode`, MIT), with Pillow (MIT-CMU). Data
  Matrix: no pure-Python library found; the view says so and offers the document.
  Whether these libraries build for Android is to check with S013.
- The barcode sits on white in both themes, for scanners. Brightness goes to maximum
  through `ft.ScreenBrightness` where the platform allows it (not in a browser), and is
  reset on "Back".
- One page per traveller (`AdwCarousel`) is not done: each traveller's ticket is its
  own reservation, opened from its own card. To revisit with S005 (batches).
- "Ticket" on a timeline card opens it; "Open the original document" uses the copy
  kept by S014.
- Completed in 0.11.1 (defect seen on the S011 screenshots): a kept document made the
  hotel, the restaurant and the museum show "Ticket". A ticket is now a barcode, or the
  kept document of a transport or an event (an e-ticket); a stay's or a table's
  document is not something to show at a gate, so their detail offers "Booking
  document" instead. The header-bar shortcut (S021) follows the same rule.
