# ADR-0002 — A UI-independent core, asynchronous

- **Status**: accepted
- **Date**: 2026-11-24
- **Deciders**: project maintainer
- **Related stories**: S001

## Context

Flet is chosen for v1 (ADR-0001), but a native GNOME app (GTK4 + libadwaita) remains a
goal for later. Rewriting import, sync and transport logic for a second UI would double
the work and the bugs.

## Decision

The code is split into two packages in one `uv` workspace:

- `packages/escale-core`: domain, services, adapters. It **never imports Flet**; a test
  fails if any of its modules does.
- `packages/escale-flet`: the UI and its screen state.

The core API is **asynchronous** (`asyncio`). It exposes data and events; reactive
screen state stays in each UI package.

## Consequences

**Positive**
- A future `escale-gtk` imports the same core. PyGObject ≥ 3.50 integrates with asyncio
  natively (`gi.events.GLibEventLoopPolicy`).
- The core is testable without any UI, with fakes for each adapter.

**Costs / risks**
- PyGObject's asyncio support is still marked experimental upstream, and Python 3.14
  deprecates the asyncio event-loop policy system it relies on — to watch before
  starting `escale-gtk`.
- One more package boundary to respect in every story.

## Rejected alternatives

- **One package, discipline only**: the first convenient `import flet` in a service
  would go unnoticed.
- **Core as a separate service (D-Bus, CLI)**: only needed if a UI is not in Python;
  not the case for Flet or PyGObject.
