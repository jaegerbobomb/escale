# ADR-0001 — Flet, with an Adwaita look, for every platform

- **Status**: accepted
- **Date**: 2026-11-24
- **Deciders**: project maintainer
- **Related stories**: S001, S002

## Context

Escale must run on Linux and Android first, then iOS. The design (a hi-fi mockup) is
drawn with GTK4/libadwaita widgets, because the app is meant to feel at home on GNOME.
GTK does not run on Android or iOS in any usable way. The maintainer is fluent in
Python and wants a usable multi-platform app quickly.

## Decision

We build the UI with **Flet ≥ 1.1** (Python, rendered by Flutter) for Linux, Android and
iOS, with a theme that imitates Adwaita (colours, typography, density, light and dark).
The libadwaita widgets of the mockup are mapped to Flet controls (table in `SPEC.md`).

## Consequences

**Positive**
- One UI code base for three platforms, in the maintainer's language.
- Flet 1.0 (September 2026) is declared production-ready; 1.1 adds responsive sizing
  (`min_width`/`max_width`), local notifications and a neutral theme close to Adwaita.

**Costs / risks**
- The look is imitated, not native: no libadwaita widgets, no GNOME accessibility stack
  for free. Acceptable for v1; a native GNOME app stays possible on the same core
  (ADR-0002).
- An Adwaita look will feel foreign on iOS. To be decided when iOS starts: same look
  everywhere, or Flet's adaptive (Cupertino) controls on iOS.
- Flet 1.x broke compatibility with 0.28: only 1.1+ documentation applies.

## Rejected alternatives

- **GTK4 + libadwaita (PyGObject)**: native on GNOME, but no Android or iOS.
- **Rust core + native UIs (gtk-rs, Compose, SwiftUI via UniFFI)**: the cleanest result
  everywhere, but three UIs to write and maintain — far longer before a first usable
  app.
- **Rust UI toolkits (Slint, Dioxus, Tauri 2)**: possible on all three platforms, but
  either young on mobile (Slint iOS is a tech preview, Dioxus mobile renderer is
  younger than its desktop one) or web-based (Tauri), with no gain over Flet for v1.
