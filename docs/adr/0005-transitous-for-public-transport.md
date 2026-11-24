# ADR-0005 — Transitous for public transport data; no flight tracking in v1

- **Status**: accepted
- **Date**: 2026-11-24
- **Deciders**: project maintainer
- **Related stories**: (epic `live`)

## Context

KDE Itinerary gets journeys and real-time data through KPublicTransport, a C++ library
with Transitous plus about 70 operator services. There is no Python binding.
Transitous is a community-run, provider-neutral routing service built on MOTIS, with a
public API, used by KDE Itinerary and GNOME Maps.

In KDE Itinerary, a flight imported from a PDF gets no live data: real-time queries only
run for flights already tied to a journey from a public transport search, which in
practice rarely covers flights.

## Decision

- Escale uses the **Transitous API** directly over HTTP for station search, journey
  search, real-time data and alternatives.
- Every network source can be disabled individually.
- **Flights have no live tracking in v1.** Each segment shows whether it is tracked and
  why not; "Refresh" is enabled only when something can be refreshed. A flight-status
  source may be added later (most are paid).

## Consequences

**Positive**
- One open, documented API; no C++ dependency.

**Costs / risks**
- Fewer real-time sources than KPublicTransport. Coverage of the lines the users
  actually take, and the API's usage terms, must be checked (investigation issue).
- No live data for flights, stated plainly in the UI instead of a silent no-op.

## Rejected alternatives

- **Bind KPublicTransport**: no binding, C++/Qt dependency on every platform.
- **Operator APIs one by one**: endless maintenance.
