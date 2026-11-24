# CLAUDE.md — operational conventions (composed by story-spec)

> ⚙️ **File composed** by `story-spec init` from the core + the modules declared in
> `.story-spec/manifest.yaml`. Do not edit the `@import` blocks by hand: re-run
> `story-spec init --sync` after changing the manifest. **Project-specific** content
> (stack, commands, house rules) goes under "Project-specific".

## Core

@.story-spec/core/CLAUDE.core.md

## Enabled modules

<!-- BEGIN story-spec:modules (generated) -->
@.story-spec/modules/adr/CLAUDE.md
@.story-spec/modules/story-lint/CLAUDE.md
@.story-spec/modules/release-versioning/CLAUDE.md
@.story-spec/modules/claude-code/CLAUDE.md
@.story-spec/modules/docs-diataxis/CLAUDE.md
@.story-spec/modules/visual-review/CLAUDE.md
<!-- END story-spec:modules -->

## Project-specific

<!-- Everything that does not come from story-spec: stack, versions, make commands, house rules. -->

- **What this is**: Escale, a privacy-first travel companion (Linux and Android first,
  iOS later), a GNOME-styled cousin of KDE Itinerary. Start with
  `docs/explanation/vision.md`, then the project spec `SPEC.md`, then
  `docs/explanation/roadmap.md` for the order of work.
- **Stack**: Python ≥ 3.12, Flet ≥ 1.1, asyncio. Two packages:
  `packages/escale-core` (no Flet import, ever — a test enforces it) and
  `packages/escale-flet` (the UI). See ADR-0002.
- **Tooling**: `uv` (workspace), `ruff` (lint + format), `mypy` (strict on the core),
  `pytest` + `pytest-bdd`.
- **Commands** (after `uv sync --all-packages`):
  `uv run ruff check`, `uv run ruff format --check`, `uv run mypy`,
  `uv run pytest`.
- **Quality check before commit**:
  `uv run ruff check && uv run ruff format --check && uv run mypy && uv run pytest`.
- **Stories**: `python3 scripts/lint_stories.py --stories-dir=stories --strict`.
  Generated features go to `tests/features/` (gitignored).
- **Language**: everything in the repository is written in English.
- **Licence**: GPL-3.0-or-later with the App Store notice in `COPYING.iOS` (ADR-0006).
  Do not copy code from projects whose licence is incompatible with GPL-3.0; do not
  vendor GPL code written by others into the iOS build.
- **Investigations** (things to check before deciding) are GitHub issues labelled
  `investigation`, not stories. Their outcome is recorded in an ADR or in the
  story they unblock.
- **Screens are validated from screenshots**: a PR that adds or changes a screen is
  validated by the maintainer from screenshots **shown in the Claude Code session**, not
  only attached to the PR. Capture every new or changed view at 1000, 500 and 380 px,
  light and dark, from the PR's head, and show them before asking for validation. No
  screenshots, no validation request. Capture with `uv run python tools/screenshots.py`
  (see `docs/how-to/capture-screenshots.md`); add any new view to its `VIEWS`.
- **Never** put a chat or session link in a commit, PR or issue.
