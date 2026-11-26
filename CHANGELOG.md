# Changelog

All notable changes to Escale are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.17.0] - 2026-11-26

### Added
- S006a: the core connects to a Nextcloud account (CalDAV and WebDAV through
  `caldav`): checks the app password, lists the calendars, creates the "Trips" calendar
  on request and the "Escale" folder, and says why a connection failed (refused,
  unreachable, not a Nextcloud). Tested against a real Nextcloud in a CI job. No screen
  yet: the preferences come with S006b.

### Changed
- S006 split into S006a (core) and S006b (preferences); S007 no longer waits for S005
  (one event per reservation until batches exist); S025, S028, S029, S030 and S035
  validated.

## [0.16.0] - 2026-11-26

### Changed
- S062: a train's or a flight's detail looks like the mockup: number and kind, a card
  with departure and arrival times large, stations or airports, platform or terminal,
  the duration, the time zones when they differ; seat and class as chips; "Show
  Ticket" wide at the bottom.

## [0.15.0] - 2026-11-26

### Changed
- S061 (ADR-0008): a booking's detail and the stay editor follow the GNOME HIG. Back
  ("‹ trip") is at the left of the header bar and Edit (a pencil) at its right; a
  detail has one main button ("Ticket" or "Manage booking on …"), the other actions are
  rows. The stay editor is a dialog with Cancel, then Save; Return saves, Esc cancels;
  on a phone it is a bottom sheet. "Add" moves to the left of the header bar; header
  bar buttons are flat.

## [0.14.0] - 2026-11-25

### Added
- S017b: "Edit" on a stay's detail opens its editor (name, address, coordinates,
  check-in and check-out, room, contact, booking reference, names). "Save" stays
  disabled while the name or the times are missing, or the check-out is not after the
  check-in. Saved stays keep their place's time zone.

## [0.13.0] - 2026-11-25

### Added
- S017a: a stay's detail shows its full address, room, contact (telephone, e-mail and
  website open in the system's apps), booking status, and "Manage booking on <site>"
  when the confirmation gives a link (Booking.com, Airbnb, …).

### Changed
- S017 split into S017a (stay detail) and S017b (stay editor).

## [0.12.0] - 2026-11-25

### Added
- S016: "Share flight" in a flight's detail shares a Flightradar24 link to follow it
  live (share sheet on phones, copied elsewhere). The airline's ICAO code comes from a
  table built from Wikidata (CC0); no link when the airline is not known for sure.

### Changed
- The segment detail's actions ("Ticket", "Share flight") sit on a row under the title.

## [0.11.1] - 2026-11-25

### Fixed
- S015: hotels and restaurants no longer show "Ticket" just because their booking file
  was kept; a ticket is a barcode, or the kept document of a transport or an event.
  Their detail offers "Booking document" instead.
- S020: an outing's row no longer repeats the place name under the title; it shows the
  venue when it differs from the title, and the street.

## [0.11.0] - 2026-11-24

### Added
- S011: jump index and segment detail. A "Jump to" panel left of the timeline (a menu
  on a medium window, a bottom sheet on a narrow one) scrolls to a booking and
  highlights it. Clicking a booking opens its detail; "‹ <trip>" goes back to the same
  place with the card highlighted. On a narrow window the detail hides the bottom bar.

## [0.10.0] - 2026-11-24

### Changed
- S020: "Current" looks like the mockup: accented "next" card with a "NEXT" band, other
  bookings in a boxed list, large departure and arrival times, pill badges (platform,
  seat, nights, "Confirmed"), connection rows between legs, avatars and traveller count
  in the header.

## [0.9.0] - 2026-11-24

### Added
- S021: "Ticket" in the header bar, on every tab, opens the active trip's next ticket
  full screen, when it has one (an icon next to "+" on a narrow window).

## [0.8.0] - 2026-11-24

### Added
- S015: "Ticket" on a timeline card opens the ticket full screen: number, route, date,
  coach and seat, travellers, the barcode on white (QR, Aztec, PDF417, Code 128, drawn
  on the device, no network) and the ticket number; screen brightness up where the
  platform allows. Without a barcode, it opens the original document.
- Story S020: the current trip as in the mockup (after S015).

## [0.7.0] - 2026-11-24

### Added
- S010b: "Current" shows the active trip: name, dates, travellers, and a timeline of
  cards (train or flight with times, stations, platform, seat and duration; hotel with
  nights and check-in/out; events with time and place). The next segment is outlined
  with "Next · leaves in …". It reloads after an import.

## [0.6.0] - 2026-11-24

### Added
- S010a: reservations are grouped into trips and outings (core): a trip goes on while
  bookings follow within a day or until the way back; an outing is one day with no
  lodging and no long-distance transport. The active trip is the one in progress, else
  the next.
- Stories S010a, S010b, S010c (S010 split) and S016 ready.

### Changed
- "Add" is a split button as in the mockup (7 px radius, no shadow, 1 px separator), and
  its menu has the mockup's six entries; only "Import a file…" works yet.

## [0.5.0] - 2026-11-24

### Added
- S014: imports are kept on the device, in SQLite under `~/.local/share/escale`, with a
  copy of each ticket file (`documents/<sha256>/`, KDE Itinerary's layout). Importing
  the same booking twice saves it once.
- Stories S015 (full-screen offline ticket) and S016 (share a flight on Flightradar24).

### Changed
- Roadmap: the `timeline` epic (trips, tickets) comes before `sync`. S005 deferred.
- CI uses `actions/checkout@v7` (Node 24).

## [0.4.0] - 2026-11-24

### Added
- S004: import with confirmation. "Add" and "Add → Import a file…" open the file
  chooser; a bottom sheet shows what was found (train or flight number, route, date,
  travellers, "New trip") and saves only on "Add to trip". Nothing recognised or an
  unreadable file offers "Add manually" (disabled until manual entry exists). On
  Android and iOS the entry explains that tickets are read on Linux.
- `ReservationStore` port in the core, with an in-memory store (persistence: S014).
- Story S014 (local store in SQLite), proposed.
- Demo mode for screenshots of the import sheets (`ESCALE_DEMO=1`).

## [0.3.0] - 2026-11-24

### Added
- S003: ticket extraction in the core through `kitinerary-extractor` (subprocess with a
  timeout, found on `PATH`, at a configured path or where Linux distributions install
  it); reservations keep their raw JSON-LD and link the file by its SHA-256. A missing
  extractor or an unreadable file is an error result, not a crash.

### Changed
- CI installs `kitinerary-extractor` and requires the adapter tests to run against it.

## [0.2.0] - 2026-11-24

### Added
- S002: adaptive shell with three views (Current, My trips, Statistics); tabs in the
  header from 550 px, in a bottom bar below; "Add" split button; Adwaita-like theme,
  light and dark following the system, state colours as tokens; Adwaita Sans font.
- `escale` command (`python -m escale_flet`), `--web` to serve the app locally.
- Screenshot tool for visual review (`tools/screenshots.py`), run by CI as an artifact;
  `visual-review` module enabled.

### Changed
- The quality check runs `uv run mypy`, which also checks `tools/`.

## [0.1.0] - 2026-11-24

### Added
- S001: `uv` workspace with `escale-core` and `escale-flet`; a boundary test that fails
  and names the module when the core imports Flet; ruff, mypy (strict on the core),
  pytest and pytest-bdd; a `Quality` CI workflow on every pull request.
- Project plan: vision, roadmap, project spec (`SPEC.md`), ADRs 0001–0007, design notes.
- First thirteen stories (S001–S013), status `proposed`.
- StorySpec kit (vendored from jaegerbobomb/story-spec@8f0ae8d) with the `adr`,
  `story-lint`, `release-versioning`, `claude-code` and `docs-diataxis` modules.
- Licence: GPL-3.0-or-later, App Store notice, contribution terms.

[Unreleased]: https://github.com/jaegerbobomb/escale/compare/v0.17.0...HEAD
[0.17.0]: https://github.com/jaegerbobomb/escale/compare/v0.16.0...v0.17.0
[0.16.0]: https://github.com/jaegerbobomb/escale/compare/v0.15.0...v0.16.0
[0.15.0]: https://github.com/jaegerbobomb/escale/compare/v0.14.0...v0.15.0
[0.14.0]: https://github.com/jaegerbobomb/escale/compare/v0.13.0...v0.14.0
[0.13.0]: https://github.com/jaegerbobomb/escale/compare/v0.12.0...v0.13.0
[0.12.0]: https://github.com/jaegerbobomb/escale/compare/v0.11.1...v0.12.0
[0.11.1]: https://github.com/jaegerbobomb/escale/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/jaegerbobomb/escale/compare/v0.10.0...v0.11.0
[0.10.0]: https://github.com/jaegerbobomb/escale/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/jaegerbobomb/escale/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/jaegerbobomb/escale/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/jaegerbobomb/escale/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/jaegerbobomb/escale/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/jaegerbobomb/escale/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/jaegerbobomb/escale/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jaegerbobomb/escale/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jaegerbobomb/escale/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jaegerbobomb/escale/releases/tag/v0.1.0
