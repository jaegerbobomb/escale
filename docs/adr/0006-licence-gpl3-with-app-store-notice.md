# ADR-0006 — GPL-3.0-or-later, with an App Store notice

- **Status**: accepted
- **Date**: 2026-11-24
- **Deciders**: project maintainer
- **Related stories**: —

## Context

The maintainer wants a licence as close to the GPL as possible, following GNOME's
practice, and compatible with distribution on Apple's App Store. GNOME requires an
OSI-approved licence and prefers copyleft; most recent GNOME applications use
GPL-3.0-or-later. The GPL and the App Store terms are widely considered in conflict
(VLC was pulled from the App Store in 2011 after a contributor objected). A copyright
holder can always grant extra permissions on their own code. The Nextcloud iOS app,
under GPLv3+, ships a `COPYING.iOS` notice in which its copyright holders commit not
to pursue a violation that results solely from that conflict.

## Decision

- Escale is licensed under **GPL-3.0-or-later** (`LICENSE`).
- `COPYING.iOS` states that the copyright holders will not enforce a violation that
  results solely from the App Store terms, as long as the rest of the GPL is respected
  (source available, licence text provided).
- Contributions are accepted under the same terms, signed off with the Developer
  Certificate of Origin (`CONTRIBUTING.md`).
- Third-party GPL code is not vendored into the iOS build; dependencies must be
  GPL-3.0-compatible (Flet: Apache-2.0; `caldav`: GPL-3.0 or Apache-2.0;
  `kitinerary-extractor`: LGPL, run as a separate process, not shipped on iOS).

This is not legal advice; it records the project's intent.

## Consequences

**Positive**
- Strong copyleft, as in GNOME; eligible for GNOME Circle on the licence criterion.
- A documented path to the App Store.

**Costs / risks**
- The notice binds only code whose authors agreed to it: contributions without the
  sign-off cannot ship to iOS.
- Fallback if the notice is ever insufficient: relicense to **MPL-2.0** (weak copyleft,
  used by Firefox for iOS and Brave), which requires every contributor's agreement.

## Rejected alternatives

- **MPL-2.0 now**: App Store-friendly without debate, but file-level copyleft only —
  further from the GPL than the maintainer wants.
- **MIT / Apache-2.0**: no copyleft.
- **Plain GPL-3.0 without notice**: blocks iOS.
