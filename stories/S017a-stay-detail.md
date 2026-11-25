---
id: S017a
title: "Stay detail"
epic: timeline
depends_on: [S010b, S011]
status: done
estimate: S
bdd: true
updated: "2026-11-25"
released_in: "0.13.0"
---

## User story

> **As a** traveller, **I want** to see everything about where I sleep, **so that** the
> address, the times, the contact and the booking are at hand when I arrive.

## Technical description

- Child of S017. A stay (`LodgingReservation`) opens from its card onto S011's detail:
  name; full address (street, postal code, city, region, country); check-in and
  check-out, in the place's own time (the offset of the JSON-LD); room
  (`lodgingUnitDescription`); contact (telephone, e-mail, website of the
  `LodgingBusiness`); booking (reference, under name, cancelled or not); the kept
  document ("Booking document", 0.11.1).
- Telephone, e-mail and website are actionable through the system (`tel:`, `mailto:`,
  the browser).
- **Manage the booking.** When the JSON-LD carries a link to the booking — a
  `potentialAction` (`UpdateAction`, then `ViewAction`) with a `target`,
  `modifyReservationUrl`, or the reservation's `url`, as KItinerary extracts from
  Booking.com or Airbnb confirmations — the detail shows "Manage booking on <site>",
  which opens it in the browser. Escale never logs into those sites.

## Acceptance Criteria

### Scenario: The detail of a stay

* **Given** a stored stay at "The Hoxton, Holborn" from 8 July 15:00 to 10 July 11:00
* **When** the user opens its card
* **Then** the detail shows the name, the address, the check-in and the check-out

### Scenario: The booking can be managed on its site

* **Given** a stay imported from a Booking.com confirmation with a link to manage the booking
* **When** the user opens its detail
* **Then** a "Manage booking on Booking.com" action is shown

### Scenario: The hotel can be called

* **Given** a stored stay whose hotel has a telephone number
* **When** the user opens its detail and taps the telephone
* **Then** the system is asked to call that number

## Notes

- Split from S017 (2026-11-25, validated by the maintainer). The editor is S017b.
- Delivered in 0.13.0. The detail rows: check-in, check-out, address (street, postal
  code and town, region, country), room, telephone, e-mail, website, travellers,
  booking reference, and "Status: Cancelled" when it is. Times are shown in the offset
  the JSON-LD gives, which is the place's own time.
- Links are handed to the system with `ft.UrlLauncher` (`tel:` with spaces removed,
  `mailto:`, the website). Only `http(s)` links from imported data are opened.
- "Manage booking on <site>": `UpdateAction` target, then `modifyReservationUrl`, then
  `ViewAction` target, then the reservation's `url` (KItinerary 23.08 knows all four).
  The site is "Booking.com" or "Airbnb" when the host is theirs, else the host name.
- The kept document stays the "Booking document" action (0.11.1); a list of every
  document of a booking can come with S009.
- Demo route `/stay-detail` and screenshot view `stay-detail`; the demo hotel's contact
  is made up (`+44 20 7946 0000` is in Ofcom's range for drama, `example.com`).
- Layout (2026-11-25, after the maintainer found the first version, a flat list of
  rows, ugly): the mockup's "Nuit d'hôtel" screen — identity (icon tile, name,
  address), a strip with check-in, check-out (time large, day below) and the number of
  nights, the booking's facts and the contact as label/value rows with icons, then the
  actions ("Manage booking on <site>" filled, "Booking document"). The mockup's photo,
  price, "Itinéraire" (S022) and map need data or stories not there yet.
