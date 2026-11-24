# Changelog

All notable changes to Escale are documented here.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/jaegerbobomb/escale/compare/v0.5.0...HEAD
[0.5.0]: https://github.com/jaegerbobomb/escale/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/jaegerbobomb/escale/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/jaegerbobomb/escale/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/jaegerbobomb/escale/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/jaegerbobomb/escale/releases/tag/v0.1.0
