# Roadmap

Ten epics, in order. Each has a goal and **exit criteria**: the epic is finished when
every box is ticked, not when its last story is merged. The stories of an epic are the
files in `stories/` whose `epic:` field names it.

> This page plays the role of the `epics` module proposed in
> [jaegerbobomb/story-spec#9](https://github.com/jaegerbobomb/story-spec/pull/9). Once it
> is merged, each section moves to `epics/<epic>.md`.

The MVP is `foundation`, `import`, `timeline` and `sync` (whether `outings` joins it is
the maintainer's call).

**Priority (maintainer, 2026-11-24):** be close to KDE Itinerary on Android, and first
in what it shows: trips, timeline, tickets. So `timeline` comes before `sync`; imports
are kept locally (S014) until the sync exists.

## 1. `foundation` — the workspace and the shell

**Goal.** A repository where every story can be built and tested, and an empty app
window that already adapts to its width.

- [x] `uv` workspace with `escale-core` and `escale-flet`; a test fails if the core imports Flet
- [x] CI runs ruff, mypy, pytest and the story linter on every PR
- [x] The app window shows the three tabs, and moves them to a bottom bar under 550 px
- [x] Adwaita-like theme, light and dark, with the state colours as tokens

## 2. `import` — tickets in, on Linux

**Goal.** Real tickets become reservations, never silently.

- [ ] About ten real tickets (SNCF, Eurostar, SNCB, a hotel, a concert) import correctly
- [ ] Every import goes through a confirmation; a failed extraction opens a pre-filled manual entry
- [ ] The same ticket imported twice does not duplicate; a second traveller joins the batch
- [ ] Documents are stored by SHA-256 and linked with `subjectOf`
- [ ] A stay can be added and corrected by hand (S017, S018)
- [ ] A place shared from Google Maps or CoMaps becomes a pre-filled stay, with at most one opt-in request to Google to resolve a short link (S019)
- [ ] Booking.com and Airbnb confirmations (e-mail saved as `.eml`, PDF) import as stays with their "manage booking" link (S024)
- [ ] A stay can be completed from, or picked in, OpenStreetMap (S023)
- [ ] A file shared to Escale (Android) or opened with it (Linux) goes to the import (S025)
- [ ] A barcode can be scanned or picked and attached to a reservation (S026)
- [ ] An SNCF or Deutsche Bahn ticket can be fetched from its reference and name (S027)
- [ ] A KDE Itinerary `.itinerary` export imports with its documents and passes (S028)

## 3. `timeline` — the current trip

**Goal.** The hi-fi synthesis screen of the mockup, at the three widths.

- [ ] Automatic grouping of reservations into trips
- [ ] Timeline with the three card densities (compact, detailed, disruption)
- [ ] Jump index, segment detail, train editor with KDE Itinerary's fields
- [ ] "Back" returns to the same scroll position with the card highlighted
- [ ] Any place opens in the user's map app (S022)
- [ ] A ticket opens full screen with its barcode, offline (S015)
- [x] A flight can be shared so that someone follows it live (S016)
- [ ] Flights, buses, ferries, events, restaurants and rental cars can be edited and added by hand (S029–S031)

## 4. `outings` — evenings and days out, not only trips

**Goal.** The same engine for a dinner and a concert as for a week abroad (mockup
"Sorties — au-delà des voyages"): one or more linked events on the same evening or day,
no overnight stay, local places.

- [ ] Event, restaurant, museum and match tickets are imported and shown like transport
  (cards with time, place, ticket) (S031)
- [ ] Bookings close in time and place on the same day group into an outing (purple
  `#9141ac`), named after its events ("Concert + dinner") (S032)
- [ ] An outing's timeline shows the walk or local transport between its places, and the
  last metro or bus home (S034)
- [ ] "Add → New outing" creates one by hand (S033)
- [ ] "My trips" lists outings with trips, with an All / Trips / Outings filter
## 5. `sync` — every device sees the same trips

**Goal.** A Nextcloud account keeps Linux and Android in step, and stays readable by
KDE Itinerary. Done before the rich screens because it carries the most risk.

- [ ] A ticket imported on Linux appears on Android, with its PDF
- [ ] An edit made on Android comes back to Linux
- [ ] KDE Itinerary imports an event written by Escale
- [ ] A minimal Android build lists the synced reservations and opens their documents
- [ ] CI builds the APK on every pull request and keeps it as an artifact (S013); from then
  on, every PR that touches the app is also checked on Android

## 6. `browse` — trips, outings, statistics

- [ ] "My trips" lists upcoming and past trips and outings, filterable and searchable
  (outings themselves: epic `outings`) (S035)
- [ ] Trips can be renamed, merged, split and deleted; a reservation can move to another trip (S036)
- [ ] Statistics computed locally, per year and per trip (distance by mode, CO₂ estimate, destinations) (S037)

## 7. `live` — online data

- [ ] Train search (four-screen flow, pre-filled), added as "planned" (S044)
- [ ] Real time and alternatives through Transitous (S040, S042)
- [ ] Local transfers: home → station, station → hotel, between places (S043)
- [ ] Live status on board, for the trains and coaches that expose an on-board API (S046)
- [ ] Each segment shows whether it is tracked and why not; "Refresh" disabled with a reason when nothing can be refreshed (S038)
- [ ] Pass updates for pkpass that support them (S045)
- [ ] One switch per network source; local notifications (S039, S041)

## 8. `stations` — finding your way in the station

- [ ] Per-floor map of stations and airports from OpenStreetMap, platform highlighted (S047)
- [ ] Coach layout and the platform section where the coach stops, for the operators that publish it (S048)

## 9. `comfort`

- [ ] Country change card (currency with converter, time zone, plugs, driving side) (S049); time zone and DST markers (S050)
- [ ] Weather at arrival (S051), watched folder on Linux (S053), `.itinerary` export (S052)
- [ ] Discount cards and passes in one page (S055)
- [ ] Share a location or an arrival in a Matrix room (S056)
- [ ] A map of the trip inside Escale (flet-map), its places and segments, tiles from an opt-in source with an offline cache (S054)

## 10. `packaging`

- [ ] Linux Flatpak with the static `kitinerary-extractor` (S057); Android package
- [ ] CI builds the signed release APK from a version tag (signing key in the repository's
  secrets, never in the repository) (S058)
- [ ] First-run screen to connect the Nextcloud account (S059)
- [ ] iOS (v2): build on macOS, Apple developer account, pkpass handed to Apple Wallet (S060)
