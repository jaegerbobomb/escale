---
id: S026
title: "Add a barcode to a reservation"
epic: import
depends_on: [S015]
status: proposed
estimate: M
bdd: true
updated: "2026-11-25"
---

## User story

> **As a** traveller with a ticket only on paper or in a screenshot, **I want** to attach its barcode to the reservation, **so that** the full-screen ticket (S015) shows it at the gate.

## Technical description

- On a reservation: "Add barcode" → scan with the camera (Android) or pick an image or PDF (all platforms). KDE Itinerary has the same action ("manually add ticket barcodes to existing reservations", release notes).
- Decoding: QR, Aztec, PDF417, DataMatrix. Library to choose (GPL-compatible, works in Flet on Android); camera access in Flet to check.
- The raw barcode content is stored in the reservation's `reservedTicket.ticketToken` as KItinerary does; the image itself is not kept.
- On Linux, an image or PDF can also go through `kitinerary-extractor`, which may recognise a railway barcode (UIC 918.3, FCB) and fill the reservation (to check).

## Acceptance Criteria

### Scenario: Scan a QR code

* **Given** a train reservation without a ticket
* **When** the user scans a QR code
* **Then** the full-screen ticket shows that QR code

### Scenario: Nothing recognised

* **Given** a picture without any barcode
* **When** the user picks it
* **Then** Escale says no barcode was found and changes nothing

## Notes

- Proposed 2026-11-25 to bring Escale close to KDE Itinerary on Android (gap review against apps.kde.org/itinerary and its release notes).
