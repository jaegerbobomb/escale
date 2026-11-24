# Roadmap

Eight epics, in order. Each has a goal and **exit criteria**: the epic is finished when
every box is ticked, not when its last story is merged. The stories of an epic are the
files in `stories/` whose `epic:` field names it.

> This page plays the role of the `epics` module proposed in
> [jaegerbobomb/story-spec#9](https://github.com/jaegerbobomb/story-spec/pull/9). Once it
> is merged, each section moves to `epics/<epic>.md`.

The MVP is epics 1 to 4.

## 1. `foundation` — the workspace and the shell

**Goal.** A repository where every story can be built and tested, and an empty app
window that already adapts to its width.

- [ ] `uv` workspace with `escale-core` and `escale-flet`; a test fails if the core imports Flet
- [ ] CI runs ruff, mypy, pytest and the story linter on every PR
- [ ] The app window shows the three tabs, and moves them to a bottom bar under 550 px
- [ ] Adwaita-like theme, light and dark, with the state colours as tokens

## 2. `import` — tickets in, on Linux

**Goal.** Real tickets become reservations, never silently.

- [ ] About ten real tickets (SNCF, Eurostar, SNCB, a hotel, a concert) import correctly
- [ ] Every import goes through a confirmation; a failed extraction opens a pre-filled manual entry
- [ ] The same ticket imported twice does not duplicate; a second traveller joins the batch
- [ ] Documents are stored by SHA-256 and linked with `subjectOf`

## 3. `sync` — every device sees the same trips

**Goal.** A Nextcloud account keeps Linux and Android in step, and stays readable by
KDE Itinerary. Done before the rich screens because it carries the most risk.

- [ ] A ticket imported on Linux appears on Android, with its PDF
- [ ] An edit made on Android comes back to Linux
- [ ] KDE Itinerary imports an event written by Escale
- [ ] A minimal Android build lists the synced reservations and opens their documents

## 4. `timeline` — the current trip

**Goal.** The hi-fi synthesis screen of the mockup, at the three widths.

- [ ] Automatic grouping of reservations into trips
- [ ] Timeline with the three card densities (compact, detailed, disruption)
- [ ] Jump index, segment detail, train editor with KDE Itinerary's fields
- [ ] "Back" returns to the same scroll position with the card highlighted

## 5. `browse` — trips, outings, statistics

- [ ] "My trips" lists upcoming and past trips and outings, filterable and searchable
- [ ] Statistics computed locally (distance by mode, CO₂ estimate, destinations)

## 6. `live` — online data

- [ ] Train search (four-screen flow, pre-filled), added as "planned"
- [ ] Real time and alternatives through Transitous
- [ ] Each segment shows whether it is tracked and why not; "Refresh" disabled with a reason when nothing can be refreshed
- [ ] Pass updates for pkpass that support them
- [ ] One switch per network source; local notifications

## 7. `comfort`

- [ ] Country change card (currency, time zone, plugs, driving side)
- [ ] Weather at arrival, full-screen offline ticket, watched folder on Linux, `.itinerary` export

## 8. `packaging`

- [ ] Linux package with the static `kitinerary-extractor`; Android package
- [ ] First-run screen to connect the Nextcloud account
- [ ] iOS (v2): build on macOS, Apple developer account, pkpass handed to Apple Wallet
