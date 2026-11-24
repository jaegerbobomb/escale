---
id: S020
title: "Current trip looks like the mockup"
epic: timeline
depends_on: [S010b]
status: done
estimate: M
bdd: false
updated: "2026-11-24"
released_in: "0.10.0"
adr: [1]
---

## User story

> **As a** traveller, **I want** the current trip to look like a GNOME app, as in the
> mockup, **so that** it is pleasant and quick to read.

## Technical description

The maintainer validated S010b's screenshots but found them far from the mockup
("Voyage en cours — desktop" and "Carte-segment — 3 densités", card 1b). Bring the view
close to it, with what the data already allows:

- **Header**: trip title in the page (`AdwWindowTitle`-like), dates, travellers as
  round avatars with initials and their count ("2 travellers").
- **Timeline as a boxed list** (`.boxed-list`): rows separated by 1 px lines in one
  rounded block, not loose cards; the next segment as an accented card (`.card .accent`)
  with a "NEXT · leaves in 40 min" tag.
- **Train / flight row**: number as title with class badge ("1st class") and status
  badge (state colours, S002 tokens); departure and arrival as a two-line time column
  with a vertical line between them, station and "Platform 6" on the right; "Coach 15 ·
  Seat 42" and "1 h 22 · Direct" as dim captions; a "Ticket" button (S015) and an
  expander for "Stops & details" (stops when known).
- **Between segments**: connection time ("Connection of 20 min at Bruxelles-Midi"),
  shown as a thin row.
- **Lodging row**: name, street, "2 nights", a "Confirmed" badge, check-in and
  check-out as two labelled columns.
- Typography and spacing from libadwaita: 12 px card radius, 6/12/18 px spacing, dim
  labels for captions, Adwaita Sans weights.
- Screenshots compared side by side with the mockup in the PR.

## Acceptance Criteria

### Scenario: Validated on screenshots

* **Given** the demo trip at 1000, 500 and 380 px, light and dark
* **When** the maintainer compares the screenshots with the mockup
* **Then** the maintainer validates the look

## Notes

- Asked by the maintainer when validating S010b (2026-11-24): "c'est moche, c'est encore
  loin du design; corrige ça dans un deuxième temps". Validated (`todo`) on that request;
  scheduled after S015.
- Elements that need data Escale does not have yet stay out (real-time delays, strike
  banner, weather, local routes, alternatives).
- Delivered in 0.10.0, measurements taken from the mockup's markup: next card with a
  2 px accent border, 14 px radius, accent shadow and a full-width "NEXT · leaves in …"
  band; other segments in a boxed list (12 px radius, 1 px separators); 26 px bold
  times with a short line between departure and arrival; pill badges (24 px, 12 px
  bold: neutral for platform, seat and nights, green for "Confirmed"); a connection row
  between two legs at the same station within 6 h; header with the trip name in 26 px,
  "dates · N travellers" and round avatars with initials. The theme gains `tertiary` =
  the success colour.
- Not yet: class and status badges need data the import does not give reliably
  (status needs real time); expandable stops; the "Ticket" button stays on each card.

