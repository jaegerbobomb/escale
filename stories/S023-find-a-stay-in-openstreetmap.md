---
id: S023
title: "Find a stay in OpenStreetMap"
epic: import
depends_on: [S018]
status: proposed
estimate: M
bdd: true
updated: "2026-11-24"
---

## User story

> **As a** traveller, **I want** Escale to find my hotel in OpenStreetMap, **so that**
> its address, coordinates and phone number fill themselves in, and I can pick a place
> to stay near my destination without typing it.

## Technical description

- **Source.** OpenStreetMap lodgings: `tourism=hotel | guest_house | hostel | motel |
  apartment | chalet | camp_site`, with their tags `name`, `addr:*`, coordinates,
  `phone`, `email`, `website`, `stars`. The same data CoMaps shows.
- **Network source "Places from OpenStreetMap"**, off by default, like "Address lookup"
  (S019). Its description names the services contacted. Disabled, both actions below
  are hidden.
- **1. Complete a stay.** On a stay with a name and a town but missing address,
  coordinates or contact (imported, typed, or shared without coordinates): "Complete
  from OpenStreetMap" looks for lodgings with that name near the town (Nominatim search
  with `extratags`, as KDE Itinerary does), shows the candidates, and fills only the
  **empty** fields of the chosen one — never overwrites what the user or the ticket gave.
- **2. Pick a stay near a place.** "Add → Add manually… → Stay → Search nearby": a
  town, a station or the destination of the current trip; Escale lists the lodgings
  around it (Overpass `around` query, within a radius the user can widen), with name,
  kind, stars and distance. Choosing one opens the stay editor of S018 pre-filled; the
  dates are left for the user to set.
- Usage policies: identified user agent; Nominatim at most one request per second;
  Overpass public instance within its daily limit (10,000 requests); results cached for
  the session. Attribution "© OpenStreetMap contributors" where results are shown.
- The OSM object's link (`openstreetmap.org/<type>/<id>`) is kept with the place, so
  S022 can open it and the user can fix the data in OSM.
- No prices, no availability: OpenStreetMap describes places, it does not sell rooms.

## Acceptance Criteria

### Scenario: Completing a stay from OpenStreetMap

* **Given** the source "Places from OpenStreetMap" is enabled
* **And** a stay "Hôtel du Nord" in Paris without address nor coordinates
* **When** the user chooses "Complete from OpenStreetMap" and picks the first candidate
* **Then** the stay has the candidate's address and coordinates
* **And** its name is unchanged

### Scenario: Fields given by the user are kept

* **Given** the source "Places from OpenStreetMap" is enabled
* **And** a stay "Hôtel du Nord" in Paris whose telephone was typed by the user
* **When** the user completes it from a candidate with another telephone
* **Then** the stay keeps the telephone typed by the user

### Scenario: Picking a stay near the destination

* **Given** the source "Places from OpenStreetMap" is enabled
* **And** OpenStreetMap has three guest houses within 2 km of the trip's destination
* **When** the user searches stays nearby
* **Then** the three guest houses are listed with their distance
* **And** choosing one opens the stay editor with its name and address

### Scenario: The source is disabled

* **Given** the source "Places from OpenStreetMap" is disabled
* **When** the user opens a stay without address
* **Then** no "Complete from OpenStreetMap" action is shown
* **And** no network request is made

## Notes

- Proposed 2026-11-24, after the maintainer noted that CoMaps and Organic Maps show
  hotels: CoMaps shows only OpenStreetMap's (its FAQ); Organic Maps' Booking.com data
  came from MAPS.ME's partnership, which needs an affiliate account — not for Escale.
