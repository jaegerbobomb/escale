# Escale

A privacy-first travel companion: train, bus and flight tickets, hotel bookings and
event tickets in one timeline per trip, with real-time updates, kept in step across
your devices through your own Nextcloud. A GNOME-styled cousin of
[KDE Itinerary](https://apps.kde.org/itinerary/).

**Status: early development.** On Linux, a ticket file can be imported, confirmed and
kept on the device ([S004](stories/S004-import-confirmation.md),
[S014](stories/S014-local-store-sqlite.md)); "Current" shows the trip in progress or the
next one as a timeline ([S010b](stories/S010b-current-trip-timeline.md)).

| Read | For |
|---|---|
| [Vision](docs/explanation/vision.md) | what Escale is, what it reuses from KDE Itinerary |
| [Roadmap](docs/explanation/roadmap.md) | the eight epics, in order, with their exit criteria |
| [SPEC.md](SPEC.md) | architecture, data model, formats, UI rules |
| [Decisions](docs/adr/README.md) | why Flet, why Nextcloud, why this licence… |
| [Stories](stories/) | the work, one file per user story |
| [Design](docs/design/README.md) | the reference mockup |

## Platforms

Linux and Android first, iOS next — one [Flet](https://flet.dev) UI over a Python core
that does not depend on it, so a native GNOME app can follow.

## How the work is organised

The project follows [StorySpec](https://github.com/jaegerbobomb/story-spec): every
feature starts as a story (`stories/S<NNN>-*.md`, status `proposed`), is validated by
the maintainer, then implemented tests first. Structural choices are ADRs. Questions to
investigate before deciding are GitHub issues labelled `investigation`.

## User stories

| Story | Title | Epic | Status |
|---|---|---|---|
| S001 | Workspace and core boundary | foundation | done |
| S002 | Adaptive shell with Adwaita theme | foundation | done |
| S003 | Extract a ticket with kitinerary | import | done |
| S004 | Import with confirmation | import | done |
| S005 | Merge reservations into traveller batches | import | deferred |
| S006 | Connect a Nextcloud account | sync | todo |
| S007 | Map reservations to calendar events | sync | todo |
| S008 | Two-way calendar sync | sync | todo |
| S009 | Sync ticket documents | sync | todo |
| S010 | Trip grouping and timeline | timeline | split |
| S010a | Group reservations into trips | timeline | done |
| S010b | Current trip timeline | timeline | done |
| S010c | Segment card densities | timeline | todo |
| S011 | Jump index and segment detail | timeline | done |
| S012 | Train segment editor | timeline | todo |
| S013 | Android build listing synced reservations | sync | todo |
| S014 | Local store in SQLite | import | done |
| S015 | Full-screen ticket, offline | timeline | done |
| S016 | Share a flight to follow it live | timeline | done |
| S017 | Stay detail and editor | timeline | split |
| S017a | Stay detail | timeline | done |
| S017b | Stay editor | timeline | done |
| S018 | Add a stay by hand | import | todo |
| S019 | Import a shared place (Google Maps, CoMaps, OpenStreetMap) | import | todo |
| S020 | Current trip looks like the mockup | timeline | done |
| S021 | Shortcut to the current ticket | timeline | done |
| S022 | Open a place in a map app | timeline | todo |
| S023 | Find a stay in OpenStreetMap | import | todo |

## Licence

GPL-3.0-or-later ([LICENSE](LICENSE)), with an App Store notice
([COPYING.iOS](COPYING.iOS)). See [ADR-0006](docs/adr/0006-licence-gpl3-with-app-store-notice.md)
and [CONTRIBUTING.md](CONTRIBUTING.md).
