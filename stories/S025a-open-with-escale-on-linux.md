---
id: S025a
title: "Open a file with Escale on Linux"
epic: import
depends_on: [S004, S028]
status: done
estimate: S
bdd: true
updated: "2026-11-28"
released_in: "0.28.0"
adr: [10]
---

## User story

> **As a** traveller on Linux, **I want** to open a ticket with Escale from Files or my
> mail client, **so that** importing is one gesture, as in KDE Itinerary.

## Technical description

- Child of S025. A desktop entry, ``io.github.jaegerbobomb.Escale.desktop``, with `Exec=escale %f` and the
  MIME types Escale imports: `application/pdf`, `application/vnd.apple.pkpass`,
  `text/calendar`, `message/rfc822`, `text/html`, `image/png`, `image/jpeg`, and KDE
  Itinerary's export, `application/vnd.kde.itinerary` (checked 2026-11-28 in KDE
  Itinerary's `org.kde.itinerary.desktop` and KItinerary's
  `application-vnd-kde-itinerary.xml`, glob `*.itinerary`). That type is declared by
  KItinerary's shared-mime-info file; where KItinerary is not installed, Escale ships
  the same declaration.
- `escale FILE` starts Escale and opens the import confirmation (S004) for that file;
  an `.itinerary` file goes to S028's reader. A missing or unreadable file shows the
  confirmation's error.
- A second `escale FILE` while Escale runs opens a second window in v1 (no
  single-instance handling yet).
- The desktop entry is installed by the Linux package (S057); the repository ships it
  under `packaging/linux/`, with a how-to for installing it by hand meanwhile.

## Acceptance Criteria

### Scenario: Open a PDF with Escale on Linux

* **Given** a ticket PDF in the Files app
* **When** the user chooses "Open with Escale"
* **Then** Escale shows the import confirmation for that file

### Scenario: Open a KDE Itinerary export

* **Given** an `.itinerary` file
* **When** the user opens it with Escale
* **Then** Escale shows the import confirmation listing its reservations

## Notes

- 2026-11-28: split of S025 approved by the maintainer; application ID
  `io.github.jaegerbobomb.Escale` chosen by the maintainer (ADR-0010).
- `desktop-file-validate` passes on the desktop entry. No icon ships yet: `Icon=` names
  the application ID, and desktops show a generic icon until one is installed (S057).
- The `.itinerary` type is declared as KItinerary's CC0 `application-vnd-kde-itinerary.xml`
  declares it.
