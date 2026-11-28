---
id: S064
title: "Keep the file of a failed import"
epic: import
depends_on: [S004, S018, S030]
status: done
bdd: true
updated: "2026-11-28"
released_in: "0.32.0"
---

## User story

> **As a** traveller whose ticket Escale could not read, **I want** the file I imported to
> stay attached to the booking I then add by hand, **so that** I still have the ticket
> (its barcode, its PDF) with the booking, on every device.

## Technical description

- When an import finds nothing (S004), "Add manually" opens the chooser and then the
  editor of the chosen kind (S018, S030), as today. The import's file and document are
  kept with that editor.
- Saving adds the booking **with that document**, as an imported booking: the store
  copies the file, the booking's `subject_of` names it, and sync uploads it (S009a).
  Its detail offers the file as for an imported one: "Show Ticket" then "Open the
  original document" for a transport (S015), "Booking document" for a stay (S009b).
- The editor says which file will be attached, at the top of its form:
  "Attached: <file name>".
- Cancelling the chooser or the editor keeps nothing: no booking and no document.
- "Add manually…" from the "Add" menu, with no import before it, attaches nothing.
- The same holds for a file opened with Escale (S025a), which goes through the same
  confirmation.

## Acceptance Criteria

### Scenario: The ticket stays with a booking added by hand

* **Given** a file "coach.pdf" with no reservation was imported
* **When** the user chooses "Add manually", then "Bus", fills the trip and saves
* **Then** the bus is saved with the document "coach.pdf"
* **And** its ticket opens the original document

### Scenario: Cancelling keeps nothing

* **Given** a file "coach.pdf" with no reservation was imported
* **When** the user chooses "Add manually", then "Bus", and cancels
* **Then** no booking and no document are saved

### Scenario: Adding from the menu attaches nothing

* **Given** a file with no reservation was imported and closed
* **When** the user adds a stay from "Add → Add manually…"
* **Then** the stay is saved with no document

## Notes

- 2026-11-28: asked by the maintainer ("if an import fails, better keep the file,
  especially if it is the ticket"). S018 had left the file out.
- 2026-11-28: validated by the maintainer (`todo`), to do before S012.
- KDE Itinerary lets a document be attached to any booking afterwards; attaching any
  file to an existing booking is a separate need, not in this story.
- Delivered in 0.32.0. "Attached: <file>" sits at the top of the editor's form, not
  under it: the bus and ferry forms are long enough that a line below them is only seen
  after scrolling. For a transport the kept file is its ticket (S015): the detail
  offers "Show Ticket", whose page opens the original document.
- The file is forgotten when the chooser or the editor is cancelled or dismissed, and
  when "Add manually…" is chosen from the "Add" menu; it is kept when the editor changes
  presentation at 450 px.
