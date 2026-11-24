# ADR-0003 — Ticket extraction through `kitinerary-extractor`, Linux only in v1

- **Status**: accepted
- **Date**: 2026-11-24
- **Deciders**: project maintainer
- **Related stories**: S003, S004

## Context

KDE's KItinerary extracts reservations from PDFs, Apple Wallet passes, e-mails and iCal
files, with extractors maintained for many operators (SNCF, Eurostar, SNCB, Air
France…). It is a C++/Qt library; no Python binding was found. KDE ships a command-line
tool, `kitinerary-extractor`, that prints schema.org JSON-LD, and a fully static build
of it is used by third parties (Nextcloud Mail, Nextcloud workflow_kitinerary). The
library is LGPL-2.0-or-later.

## Decision

- Escale calls `kitinerary-extractor` as a **subprocess** and reads its JSON-LD. No
  extraction logic is rewritten in Python.
- The Linux package **ships the static binary**; a `kitinerary-extractor` found on
  `PATH` takes precedence when newer.
- **Android and iOS do not extract in v1.** Reservations reach them through the
  Nextcloud sync (ADR-0004). Manual entry and Transitous search work everywhere.

## Consequences

**Positive**
- Escale benefits from every extractor KDE maintains, for free.
- Calling a separate process keeps the LGPL library outside Escale's GPL code and
  isolates crashes on malformed documents.

**Costs / risks**
- Import on a phone requires a Linux machine somewhere in the loop.
- The static binary must be rebuilt or refreshed to get new extractors (tracked in an
  investigation issue).
- Building KItinerary for Android is possible (KDE Itinerary does it) but heavy; kept as
  a later option behind the same adapter.

## Rejected alternatives

- **Rewrite extractors in Python**: years of KDE work to redo and maintain.
- **Bind the C++ library**: no binding exists; maintaining one is out of scope.
