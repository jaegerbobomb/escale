---
id: S062
title: "Transport detail looks like the mockup"
epic: timeline
depends_on: [S011, S061]
status: proposed
estimate: S
bdd: true
updated: "2026-11-26"
adr: [8]
---

## User story

> **As a** traveller, **I want** a train's or a flight's detail to read like the
> mockup, **so that** times, stations and my seat are clear at a glance and the ticket
> is one tap away.

## Technical description

The maintainer found the flight's detail off (2026-11-26): a flat list of rows with a
small blue "Ticket" pill on top. The mockup's "Trajet en train — Aller" lays it out as:

- **Identity**: icon tile (train, plane, bus, boat), the number as title ("Eurostar
  9024", "AF 718"), a dim line below (operator or kind), a status badge when known.
- **Timeline card**: departure and arrival times large (22 px) with the time zone
  below when it differs from the device's, a dot-and-line between them, the station or
  airport in bold with platform / terminal below; the duration as a chip in between.
- **Chips**: coach and seat, class.
- **Facts rows** (as the stay, S017a): booking reference, travellers.
- **Actions at the bottom**: the main one wide, "Show Ticket" (suggested, label only
  per ADR-0008, so without the mockup's QR icon), and next to it the secondary ones as
  rows, as now ("Share flight", "Booking document").
- On a narrow window the header bar has the title, so the identity row keeps the icon
  and the dim line only (S061).
- The mockup's "Alternatives" button and status badge need real-time data (S040, S042):
  not in this story.

## Acceptance Criteria

### Scenario: A flight's detail

* **Given** a flight AF 718 from Paris Charles de Gaulle at 10:25 to London Heathrow at 10:45
* **When** the user opens its detail
* **Then** the departure and arrival times are shown large with their airports
* **And** "Show Ticket" is the only suggested button, below the details

## Notes

- Proposed 2026-11-26 after the maintainer's remark on S061's flight screenshots ("Il
  n'y a plus que le 'ticket' bleu sur la vue billet d'avion qui me gène").
