---
id: S061
title: "Detail and editor follow the GNOME HIG"
epic: timeline
depends_on: [S011, S017b]
status: done
estimate: M
bdd: true
updated: "2026-11-26"
released_in: "0.15.0"
adr: [7, 8]
---

## User story

> **As a** GNOME user, **I want** a booking's detail and its editor to behave like the
> other GNOME apps, **so that** I find back, edit, cancel and save where I expect them.

## Technical description

The maintainer found the detail's buttons and the editor's Save bar off the GNOME
guidelines (S011, S016, S017b). What the HIG says, read on developer.gnome.org on
2026-11-26:

- *Browsing*: "the standard position for the back button is the top-left"; "Header
  bars should update to reflect what is being shown in the current view."
- *Header bars*: main actions at the start, heading in the centre, menus at the end;
  "only a small number of controls"; header bar controls "should all have tooltips";
  icon or icon-and-label buttons, no label-only or suggested-style buttons in a
  primary window's header bar.
- *Buttons*: "Outside of header bars, buttons should contain either an icon or a
  label, and not both"; "Each view should only ever include a single button using
  either the suggested or destructive styles"; "Make invalid buttons insensitive".
- *Dialogs* (action dialogs): "a header bar, a heading which describes the action, and
  two primary buttons"; "the cancel button appears first"; label the affirmative
  button with an imperative verb (Save); it "should be insensitive until the required
  options have been selected"; Return activates it, Esc cancels.
- *Boxed lists* / *Text fields*: forms are boxed lists, one list per section with a
  heading; "for forms or preferences … an entry row will often be preferable".

So (ADR-0008):

- **Back** leaves the content for the header bar's start: a flat "‹ <trip>" button with
  a tooltip. The detail still replaces the content and keeps the tabs (ADR-0007).
- **Header bar in a detail**: on a narrow window the heading becomes the booking's
  title; at the end, an **Edit** icon button (tooltip "Edit") where the booking can be
  edited (stays, S017b), then the current-ticket shortcut (S021). "Add" is hidden: it
  is not about the booking shown.
- **Content actions**: at most one suggested button, label only, as a pill — "Ticket"
  when there is one, else "Manage booking on <site>". The other actions ("Share flight",
  "Booking document", "Manage booking…" when it is not the main one) are rows of a
  boxed list, each with a symbolic icon at the end.
- **The editor is an action dialog**: header with "Cancel" first, the heading "Edit
  Stay", then "Save" (suggested), insensitive while the fields are not valid; Return in
  a field saves when valid, Esc cancels. Its form is boxed lists of entry rows, one
  field per row, a heading per section. Under 450 px it is a **bottom sheet**, as
  libadwaita's `AdwDialog` presents itself in its automatic mode ("max-width: 450px or
  max-height: 360px"), closed by Cancel or by swiping it down.
- **Primary header bar**: "Add" moves to the start (main actions) as a flat split
  button; the current-ticket shortcut is a flat icon-and-label button at the end. No
  suggested or tonal style in the header bar.
- On a narrow window the header bar shows the booking's title, so the content does not
  repeat it.

## Acceptance Criteria

### Scenario: Back is at the top-left

* **Given** a segment's detail open in a window 1000 px wide
* **Then** the header bar starts with a back button named after the trip
* **And** the content has no back button

### Scenario: Edit opens an action dialog

* **Given** a stay's detail
* **When** the user clicks "Edit" in the header bar
* **Then** the editor opens as a dialog with "Cancel" before "Save"

### Scenario: Return saves the stay

* **Given** the stay editor with the check-out changed to 12:00
* **When** the user presses Return in a field
* **Then** the dialog closes and the detail shows check-out at 12:00

### Scenario: One suggested action per view

* **Given** a flight's detail with a ticket
* **Then** "Show Ticket" is the only suggested button
* **And** "Share flight" is a row

## Notes

- Asked by the maintainer (2026-11-26) after S017b: "les boutons edit, et la barre avec
  le save, ça ne me semble pas idéal avec les guidelines gnome"; written and validated
  (`todo`) at their request, to be done before S018 so later screens start right.
- Delivered in 0.15.0, with ADR-0008. HIG pages read on 2026-11-26 once
  developer.gnome.org was allowed in the environment: Header Bars, Browsing, Dialogs,
  Buttons, Boxed Lists, Text Fields.
- Back: a flat `TextButton` "‹ <trip>" (tooltip "Back to <trip>") in the header bar's
  leading slot; an icon only under 550 px, where the title is the booking's. Edit: an
  `IconButton` (pencil, tooltip "Edit") for stays only, since only stays have an editor
  so far (S012 train, S029–S031 others).
- Main action: a label-only pill `FilledButton` ("Ticket", else "Manage booking on
  <site>"); "Share flight" and "Booking document" are boxed-list rows with a symbolic
  icon at the end. The "Editing comes with a later version." note is gone.
- Editor: `ft.AlertDialog` whose title row is Cancel / "Edit Stay" / Save; fields are
  borderless text fields in boxed lists, one per row. Return submits through each
  field's `on_submit`; Esc dismisses the dialog (`on_dismiss`), checked in Chromium.
  Under 450 px: `ft.BottomSheet` with a drag handle, 90 % of the window's height;
  crossing 450 px rebuilds it with what was typed.
- 2026-11-26, review of the first screenshots, agreed by the maintainer: "Add" and the
  ticket shortcut made flat and "Add" moved to the start; the title no longer repeated
  on narrow windows. The maintainer asked whether a chevron on "Cancel" (a new screen)
  or a drawer would suit phones better: libadwaita's answer is the bottom sheet
  (`AdwDialog`, read in its documentation), so the editor is one under 450 px; "Cancel"
  keeps its label since a sheet is dismissed, not navigated back from.
- Seen while capturing, not caused by this story: the header's view switcher sometimes
  wraps "Statistics" on the first frames in the web build (font loading); to watch.
- 2026-11-26, S062: the detail's main button reads "Show Ticket" (the mockup's
  "Afficher le billet"); the scenario above says so.
