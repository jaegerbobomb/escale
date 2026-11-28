# Correct a flight

When an import got a flight wrong, or the airline gave you a gate or a new time:

1. Click the flight's card, then **Edit** (the pencil at the right of the header bar).
   The editor opens over the trip; on a phone it slides up from the bottom, and swiping it
   down closes it without saving.
2. Change what you need: the flight number (`AF 718`), and for the departure its date,
   time, boarding time, terminal and gate; for the arrival its date, time and terminal;
   your seat and the booking reference. Dates are written `2026-09-14`, times `10:25`, in
   each airport's local time: Escale keeps each airport's time zone. Instead of typing,
   the calendar button at the end of a date field and the clock button at the end of a
   time field open a picker.
3. Click **Save**, or press Return in any field.

**Save** stays greyed out while the flight cannot be saved; the reason is shown under the
form: a missing or invalid departure, a boarding time after the departure, an arrival
that is not after the departure (compared across time zones), or a flight number that
is not an airline code followed by a number.

A boarding time later than the departure's time of day, by up to four hours, is taken
as the evening before (a flight just after midnight).

The airports cannot be changed here yet. **Cancel**, or Esc, leaves the flight as it
was. Fields you leave untouched keep what the import found.
