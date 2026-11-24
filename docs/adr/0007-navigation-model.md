# ADR-0007 — Navigation model: the timeline is home, the index only jumps

- **Status**: accepted
- **Date**: 2026-11-24
- **Deciders**: project maintainer
- **Related stories**: S010, S011, S012

## Context

The mockup explored three ways to reconcile a trip's full timeline with a focused
segment view: (1a) the timeline is home and the summary is an index; (1b) a
master–detail where the timeline is the first item; (1c) purely adaptive. It also
showed that a trip has two entry points — the "Current" tab and the "My trips" list —
which explained why "back" seemed to lead to different places.

## Decision

- The stacked **timeline** is the home of a trip, on every width.
- The summary is a **jump index**: it scrolls and highlights, it never replaces the
  content. It is shown only on wide windows.
- Clicking a segment card opens its **editable detail** in place of the content, with
  "‹ <trip>" going back to the same scroll position and the card highlighted.
- Opened from "Current", a trip keeps the top-level tabs; opened from "My trips", it is
  a pushed page and the tabs give way to a back button.
- Breakpoints: **550 px** (tabs move to a bottom bar, the index becomes a "Jump to…"
  menu) and **400 px** (the detail becomes a pushed page, the index a bottom sheet) —
  libadwaita's usual thresholds, in Flet's logical pixels.

## Consequences

**Positive**
- One mental model on every device; no screen where the user wonders what "back" does.

**Costs / risks**
- Restoring the scroll position and highlight on "back" must be built explicitly.

## Rejected alternatives

- **1b, master–detail everywhere**: loses the tabs on the main screen.
- **Choosing the model per device by hand**: two UIs to maintain.
