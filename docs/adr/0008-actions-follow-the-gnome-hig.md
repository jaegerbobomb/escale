# ADR-0008 — Actions follow the GNOME HIG: header bar, one suggested action, action dialogs

- **Status**: accepted
- **Date**: 2026-11-26
- **Deciders**: project maintainer
- **Related stories**: S061, S011, S017b, S018

## Context

ADR-0001 gives Escale an Adwaita look, but the first detail and editor screens put the
back button, "Edit" and a Save bar inside the content, with several filled buttons per
view. The maintainer found them off the GNOME guidelines. The HIG (developer.gnome.org,
read 2026-11-26) places back at the top-left of the header bar, keeps header bar
controls few and with tooltips, allows one suggested or destructive button per view,
and describes editing as an action dialog (Cancel first, imperative affirmative button,
insensitive until valid). Every later screen (S018 add a stay, S012 train editor, S029–S031
other editors) will have the same questions.

## Decision

- **Back and view actions live in the header bar**: back at the start (flat, icon and
  label, tooltip); actions about the view shown (Edit…) at the end as icon buttons with
  tooltips. The header bar's content follows the view.
- **One suggested action per view**, label only, as a pill in open space; other actions
  are boxed-list rows with a symbolic icon at the end. Outside header bars a button has
  an icon or a label, not both.
- **Editing and creating happen in action dialogs**: header with Cancel first, a heading
  naming the action, an imperative affirmative button (Save, Add) in the suggested
  style, insensitive while invalid; Return activates it, Esc cancels. Forms are boxed
  lists of entry rows, one section per list. Under 450 px wide (or 360 px high) the
  dialog is a bottom sheet, as libadwaita's `AdwDialog` in its automatic presentation
  mode.
- **The primary header bar** follows the same rules: "Add" at the start as a flat split
  button, the other shortcuts flat at the end.
- The navigation model of ADR-0007 does not change.

## Consequences

**Positive**
- One convention for every detail and editor to come; screens look and behave like
  GNOME apps.

**Costs / risks**
- Flet has no libadwaita widgets: header bars, entry rows and adaptive dialogs are
  rebuilt from Material controls, and each needs checking on screenshots.
- The primary header bar departs from the mockup ("Add" was a blue split button on the
  right); the maintainer agreed (2026-11-26).

## Rejected alternatives

- **Editing inline in the detail page** (fields replace the rows): the HIG prefers
  inline editing for primary tasks, but editing a booking is occasional and must be
  cancellable as a whole.
- **Keeping actions in the content**: what the maintainer asked to change.
