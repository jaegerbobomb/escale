---
id: S001
title: "Workspace and core boundary"
epic: foundation
depends_on: []
status: done
estimate: S
bdd: false
updated: "2026-11-24"
released_in: "0.1.0"
adr: [1, 2]
---

## User story

> **As a** contributor, **I want** a workspace where the core cannot depend on the UI,
> **so that** every later story is built and tested the same way and a GTK app stays
> possible.

## Technical description

- `uv` workspace at the root with two members: `packages/escale-core`
  (`escale_core`) and `packages/escale-flet` (`escale_flet`), Python ≥ 3.12.
- `escale-flet` depends on `escale-core` and `flet>=1.1`; `escale-core` has no UI
  dependency.
- Boundary test in `escale-core`: imports every module of `escale_core` and fails if
  `flet` (or any `flet.*`) ends up in `sys.modules`; also scans the sources for
  `import flet` / `from flet` so a lazy import cannot hide.
- Tooling: ruff (lint + format), mypy (`--strict` on `escale_core`), pytest,
  pytest-bdd; `tests/features/` gitignored.
- CI (GitHub Actions) on every PR: ruff check, ruff format --check, mypy, pytest,
  `python3 scripts/lint_stories.py --stories-dir=stories --strict`.
- `.claude/hooks/session-start.sh` runs `uv sync` in remote sessions.
- No pseudo-code; no feature code in this story.

## Acceptance Criteria

### Scenario: The quality check passes on a fresh clone

* **Given** a fresh clone of the repository
* **When** `uv sync` then the quality check from `CLAUDE.md` are run
* **Then** every command exits with status 0

### Scenario: The core refuses to import Flet

* **Given** a module of `escale_core` that imports `flet`
* **When** the test suite runs
* **Then** the boundary test fails and names that module

### Scenario: CI lints the stories

* **Given** a pull request that adds a story without an `estimate` in `proposed`
* **When** CI runs
* **Then** the story lint step fails

## Notes

- `bdd: false`: this story is infrastructure; its criteria are checked by unit tests and
  by CI itself.
- 2026-11-24: validated by the maintainer (`proposed` → `todo`), delivered in 0.1.0.
- The boundary test runs two checks: a runtime probe in a fresh interpreter (imports
  every module, names the one that loads Flet) and an AST scan of the sources (catches
  lazy imports in function bodies and `importlib.import_module("flet")`). Both are
  themselves tested against a throw-away package that imports Flet.
- `scripts/` is vendored from the StorySpec kit and excluded from ruff, so it stays
  identical to upstream.
- The existing `Stories` workflow is kept; the new `Quality` workflow also lints the
  stories, on every pull request.
