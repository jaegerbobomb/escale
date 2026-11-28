# Import a ticket

On Linux, with the ticket extractor installed
([how-to](install-the-ticket-extractor.md)):

1. Click **Add**, or open the menu next to it and choose **Import a file…**. On a narrow
   window, use the **+** button.
2. Choose the file: a PDF ticket, an Apple Wallet pass (`.pkpass`), a calendar file
   (`.ics`), a KDE Itinerary export (`.itinerary`), a booking e-mail (`.eml`, `.html`) or
   a picture of the ticket's code.
3. Check what Escale found: number, route, date, travellers.
4. Click **Add to trip** to save it, or **Cancel** to leave without saving anything.

Nothing is saved before step 4.

If Escale finds nothing in the file, or cannot read it, the sheet says so. Adding the
reservation by hand will come later: the **Add manually** button is not active yet.

On a phone, importing is not available: import the file on your Linux computer, and the
reservation reaches the phone through the sync.

## Move from KDE Itinerary

In KDE Itinerary, export your data to an `.itinerary` file (its export function),
then import that file in Escale as above. Escale reads it itself, without the ticket
extractor. The sheet lists the reservations it found, says how many documents (PDFs,
pictures) come with them, and names what it leaves out: Apple Wallet passes, program
memberships (rail cards, loyalty programs), health certificates and KDE Itinerary's
settings. Escale groups the reservations into trips by itself; a file imported twice
adds nothing the second time.

Imported reservations, and a copy of each ticket file, are kept on this device under
`~/.local/share/escale`. Importing the same booking again does not duplicate it.
