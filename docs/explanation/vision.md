# Vision — why Escale exists

Escale is a privacy-first travel companion. It gathers train, bus and flight tickets,
hotel bookings and event tickets into one timeline per trip, shows what happens next
— platform, seat, delay, country change — and keeps every device in step, without an
account on anyone's server.

It is a GNOME-styled cousin of [KDE Itinerary](https://apps.kde.org/itinerary/): same
idea, same data model, and it reuses KDE's work where it can be called from outside.

## Principles

- **Local first.** Everything works offline. The only network calls are the ones the
  user enabled, source by source.
- **No account of ours.** Devices sync through the user's own Nextcloud (calendar +
  files). Escale hosts nothing.
- **Nothing silent.** An import is always confirmed; a button that cannot do anything
  says why.
- **Interoperable.** The calendar events use KDE Itinerary's format, so KDE Itinerary can
  import them; documents use its storage layout.

## What it reuses from KDE Itinerary

| Need | KDE Itinerary | Escale |
|---|---|---|
| Read tickets (PDF, pkpass, iCal, e-mail) | KItinerary extraction engine | the `kitinerary-extractor` command, shipped with the Linux app |
| Reservation data | schema.org JSON-LD | the same JSON-LD, stored as is |
| Calendar format | `X-KDE-KITINERARY-RESERVATION` | the same property |
| Document storage | `documents/<sha256>/`, `passes/` | the same layout, in Nextcloud files |
| Train editing | `TrainEditor` fields | the same fields |
| Country change card | `KItinerary::CountryInformation` | rewritten: local table + time zones |
| Journeys, real time | KPublicTransport | Transitous API directly |
| Trip grouping, multi-traveller merge | app logic, `MergeUtil` | rewritten in Python, simplified |

## Platforms

Linux and Android first, iOS next, with one Flet UI (ADR-0001). The core is a separate
Python package (ADR-0002), so a native GNOME app (GTK4 + libadwaita) can be added later
on the same logic. Tickets are extracted on Linux; phones receive them through the sync
(ADR-0003, ADR-0004).

## Design

A hi-fi mockup (GNOME/libadwaita widgets, three window widths, light and dark) defines
the screens: current trip timeline, segment detail and editor, My trips (trips and
outings), statistics, preferences, add-a-trip and train search flows, import, offline
ticket. See [docs/design/](../design/README.md).

## Status

Planning. The decisions are in [docs/adr/](../adr/README.md), the target architecture in
[SPEC.md](../../SPEC.md), the order of work in [roadmap.md](roadmap.md), and the first
stories in [stories/](../../stories/).
