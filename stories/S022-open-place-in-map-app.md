---
id: S022
title: "Open a place in a map app"
epic: timeline
depends_on: [S017]
status: todo
estimate: S
bdd: true
updated: "2026-11-24"
---

## User story

> **As a** traveller arriving somewhere new, **I want** to open my hotel, station or
> venue in my map app, **so that** I find my way with the app I already use (CoMaps,
> OsmAnd, Google Maps…).

## Technical description

- On the detail of a stay (S017), and later of any place (station, venue, restaurant):
  "Open in a map app".
- Escale builds a `geo:` URI and hands it to the system (`page.launch_url`), which lets
  the user pick the app:
  - with coordinates: `geo:<lat>,<lng>?q=<lat>,<lng>(<name>)`;
  - with only an address: `geo:0,0?q=<url-encoded address>`.
- Per platform (to confirm in tests on real devices):
  - **Android**: `geo:` is handled by map apps; CoMaps and OsmAnd open it on the place
    (OpenStreetMap wiki), Google Maps too.
  - **Linux**: `xdg-open` on the `geo:` URI; GNOME Maps is expected to handle it (to
    check). No handler → fall back to the OpenStreetMap website.
  - **iOS** (v2): no native `geo:` handling; use an Apple Plans link instead.
- Fallback everywhere: `https://www.openstreetmap.org/?mlat=<lat>&mlon=<lng>#map=17/<lat>/<lng>`
  when there are coordinates, else an OSM search for the address.
- No network call by Escale itself.

## Acceptance Criteria

### Scenario: A stay with coordinates

* **Given** a stay "Hôtel du Nord" at 48.8721, 2.3651
* **When** the user chooses "Open in a map app"
* **Then** the system is asked to open `geo:48.8721,2.3651?q=48.8721,2.3651(Hôtel du Nord)`

### Scenario: A stay with only an address

* **Given** a stay "Hôtel du Nord" at "102 Quai de Jemmapes, 75010 Paris" without coordinates
* **When** the user chooses "Open in a map app"
* **Then** the system is asked to open a `geo:0,0?q=` URI with that address

### Scenario: A stay without address or coordinates

* **Given** a stay with a name only
* **Then** no "Open in a map app" action is shown

## Notes

- Agreed with the maintainer (2026-11-24): open in the user's map app now; an embedded
  map comes later in the `comfort` epic.
- 2026-11-24: validated by the maintainer (`todo`).
