# ADR-0009 — Incoming shares through Escale's own Flet extension

- **Status**: accepted
- **Date**: 2026-11-28
- **Deciders**: project maintainer
- **Related stories**: S025, S025b, S019; investigation #19

## Context

S025 (share a ticket to Escale) and S019 (share a map link) need Escale to be a share
target on Android: listed in other apps' share sheet, and handed the shared file or
text. Investigation #19 asked whether Flet 1.1 can do this. What its sources and docs
show (read 2026-11-28 on the `v1.1.3` tag, through the GitHub mirror):

- **Being listed** is supported: `flet build` adds intent filters to the main activity
  from `[tool.flet.android.activity] intent_filter` in `pyproject.toml`
  (`flet_cli/utils/android.py`, `normalize_android_activity`).
- **Receiving the content** is not: Flet's `Share` service only shares out
  (`flet/controls/services/share.py`); nothing hands an `ACTION_SEND` intent's extras
  (`EXTRA_STREAM`, `EXTRA_TEXT`) to Python. A feature request for it exists on Flet's
  tracker (#4296, seen through a mirror, its state not checked).
- **Extensions** can fill the gap: a Python `Service` paired with a Dart `FletService`
  (`website/docs/extend/user-extensions.md`), which raises events to Python; an
  extension whose Flutter package is an Android plugin has its manifest merged by
  every build.
- The Flutter plugin `receive_sharing_intent` receives shared files and text on
  Android, and on iOS through a Share Extension target. It is Apache-2.0 (pub.dev),
  which GPL-3.0 accepts.

Not checked, because this environment cannot build an APK (the Android SDK host is
not reachable): that a share reaches Python both when Escale is closed and when it
is open, and what the iOS Share Extension costs in `flet build ios`.

## Decision

- Escale ships its own small Flet extension, `escale-share`, in this repository: a
  Python `Service` with an `on_shared` event (file paths, text), and a Dart service
  wrapping `receive_sharing_intent`, its version pinned.
- The intent filters (PDF, pkpass, `.eml`, images, `text/plain`) go in
  `[tool.flet.android.activity]`.
- Android first; iOS when ADR-0006's iOS build comes, after costing the Share
  Extension.
- Before the Android part of S025 is coded, a prototype APK checks the cold and warm
  cases on a device or an emulator, in CI or on the maintainer's machine.

## Consequences

**Positive**
- One gesture to import, as in KDE Itinerary; S019 reuses the same service for links.
- The rest of the app sees a plain Python event; nothing Android-specific leaks into
  the core.

**Costs / risks**
- Dart code to maintain, and an extension to keep in step with Flet's releases.
- `flet run` and the desktop builds without the extension show no share support;
  only `flet build` apps have it.
- If Flet adds incoming shares itself, the extension is replaced by it.

## Rejected alternatives

- **Wait for Flet**: no date; S025 and S019 would stay blocked.
- **Deep links only** (`page.route`): they carry a URL, not a shared file.
