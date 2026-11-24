# Design

The reference design is a hi-fi mockup made with Claude Design ("GNOME Travel Assistant
Design", project name *Escale*). It is drawn with GTK4/libadwaita widgets; Escale renders
it with Flet (mapping in `SPEC.md` § User interface).

It is not in this repository yet: the mockup lives in the maintainer's design tool, and
its screenshot exports were unreadable. Exporting the screens as PNG into this folder is
tracked in an issue; stories that implement a screen will then reference them.

## Pages of the mockup

1. **Synthesis (hi-fi)** — "Current trip", wide window, with the segment editor: jump
   index on the left, stacked timeline, editable train detail with KDE Itinerary's
   `TrainEditor` fields, real-time data read-only.
2. **Navigation arbitration (lo-fi)** — why the timeline is home and the index only
   jumps; the two entry points of a trip; the 3 widths × 2 states matrix (ADR-0007).
3. **Escale — GNOME travel assistant** — every other screen: current trip (desktop),
   segment master–detail with the country-change card, preferences, My trips and
   outings, the outing concept, statistics, dark theme and mobile, the three segment
   card densities, the new-trip and train-search flow, PDF import and offline ticket,
   navigation tree and component catalogue.

## Known inconsistencies to fix in the mockup

- Eurostar outbound: arrival 10:24 and seat 41 on page 1, 10:30 and seat 48 on page 3.
- Return train: 11:00 on page 1, 12:22 on page 3.
- The fourth mobile tab is "Tickets" while the desktop has "Statistics".
