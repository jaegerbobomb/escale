# Contributing to Escale

Thanks for your interest. Escale follows [StorySpec](https://github.com/jaegerbobomb/story-spec):
read `CLAUDE.md` (it holds the working rules for humans and agents alike), `SPEC.md` and
`docs/explanation/roadmap.md` first.

## How work happens

1. A feature starts as a story in `stories/` with `status: proposed`. Take its number
   with `python3 scripts/next_story_id.py --verbose`.
2. The maintainer validates it (`status: todo`). No feature code before that.
3. Tests first (red), then the implementation (green), then the quality check from
   `CLAUDE.md`.
4. One story per pull request; commit `feat(S<NNN>): <short slug>`.

Something to check before a decision can be made (does a library work on Android, does a
server keep a property…) is a GitHub issue labelled `investigation`, not a story.

## Development setup

Requires [uv](https://docs.astral.sh/uv/) and Python ≥ 3.12.

```bash
uv sync --all-packages
uv run ruff check && uv run ruff format --check && uv run mypy && uv run pytest
python3 scripts/lint_stories.py --stories-dir=stories --strict
```

The ticket extractor tests need KDE's `kitinerary-extractor` (skipped without it,
required in CI). On Debian or Ubuntu: `sudo apt install libkpim5itinerary5`.

Run the app:

```bash
uv run escale --web --port 8550           # then open http://127.0.0.1:8550
uv sync --all-packages --all-extras       # once, for the desktop window (flet-desktop)
uv run escale
```

Screens are reviewed from screenshots: `docs/how-to/capture-screenshots.md`.

`packages/escale-core` must never import Flet: `test_boundary.py` fails and names the
offending module if it does (ADR-0002).

## Licence of contributions

Escale is GPL-3.0-or-later, with the App Store notice in `COPYING.iOS`. By contributing,
you agree that your contribution is licensed under GPL-3.0-or-later **and** covered by
the commitment in `COPYING.iOS`. Without that, the iOS app could not include your code.

Sign off every commit with the [Developer Certificate of Origin](https://developercertificate.org/):

```bash
git commit -s
```

which adds `Signed-off-by: Your Name <you@example.com>`.

Do not copy code from projects whose licence is incompatible with GPL-3.0.
