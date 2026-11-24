# ADR-0004 — The user's Nextcloud is the source of truth

- **Status**: accepted
- **Date**: 2026-11-24
- **Deciders**: project maintainer
- **Related stories**: S006, S007, S008, S009

## Context

Escale runs on several devices, and only Linux can extract tickets (ADR-0003). Users of
KDE Itinerary already share data between desktop and phone through a shared calendar,
but Itinerary imports from the calendar once; it does not sync. Escale must not host
anything. The maintainer runs a Nextcloud.

KDE Itinerary's own formats, read in its source code:

- calendar export writes the reservation batch as JSON-LD in the custom property
  `X-KDE-KITINERARY-RESERVATION`, with a `KIT-` prefixed UID; documents are not
  attached;
- local storage keeps documents as `documents/<id>/meta.json` + the file, where the id
  is the SHA-256 of the content, and passes as `passes/<type>/<serial>.pkpass`;
  reservations reference documents through schema.org `subjectOf`;
- the `.itinerary` export is a zip with the same layout.

## Decision

Escale is a **connector** to an existing Nextcloud account (URL, login, app password):

- **Calendar (CalDAV)**: one event per reservation batch, in the KItinerary format, plus
  a few `X-ESCALE-*` properties. Two-way sync with sync-tokens (RFC 6578) and ETags.
- **Files (WebDAV)**: documents and passes under `Escale/`, in KDE Itinerary's layout,
  addressed by content.
- **SQLite** on each device is a cache, never the reference.

Exact formats are in `SPEC.md` § External contracts. Nextcloud is the first target; any
CalDAV/WebDAV server should work with the same code, untested.

## Consequences

**Positive**
- Every device sees the same trips; a phone gets tickets imported on Linux, with their
  PDFs.
- KDE Itinerary can still import the calendar.
- Documents cannot conflict: a changed document is a new document.
- The `.itinerary` export becomes a zip of folders that already exist.

**Costs / risks**
- Requires a CalDAV/WebDAV account; no account, no sync (the app still works locally).
- Unverified: whether Nextcloud keeps the `X-*` properties intact, and whether KDE
  Itinerary keeps `X-ESCALE-*` when it rewrites an event (investigation issues).
- Conflicts are resolved "server wins" in v1, with a notice to the user.

## Rejected alternatives

- **Import-only calendar bridge** (what KDE Itinerary does): edits on one device never
  reach the others.
- **Escale's own server**: something to host and secure, against the project's goal.
- **Documents as calendar attachments**: heavy events, poor client support, and the
  Android calendar does not support attachments or custom properties (KDE wiki).
