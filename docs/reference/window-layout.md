# Window layout

Escale has three top-level views: **Current** (the trip you are on), **My trips** and
**Statistics**. It opens on **Current**.

| Window width | Where the views are | "Add" |
|---|---|---|
| 550 px and more | a switcher in the middle of the header | button with a menu, left of the header |
| under 550 px | a bar at the bottom of the window | "+" menu, left of the header |

The layout changes as soon as the window is resized; the selected view stays selected.

The theme follows the system's light or dark preference.

A view can be opened directly by its path in the web version: `/trips`, `/statistics`.

**Current** shows the trip in progress, or else the next one: its name, dates and
travellers, then one card per booking in time order. The next one is outlined and says
how long until it leaves. With no trip ahead, the view says so.

In a trip, **Jump to** lists its bookings: a panel on the left of a wide window, a menu
next to the travellers on a medium one, a button opening a sheet on a narrow one. It
scrolls to the booking and highlights it. Clicking a booking opens its detail;
**‹ trip name**, at the left of the header bar (an arrow on a narrow window), comes back
to the same place.

In a booking's detail, the header bar follows it: its title on a narrow window, **Edit**
(a pencil) at the right when the booking can be edited, and no "Add". The main action
("Show Ticket", or "Manage booking on …" for a stay) is the one blue button; the others
("Share flight", "Booking document") are rows under the details.

A train's or a flight's detail shows its number and kind, then departure and arrival
times large with their stations or airports (and the time zone of each when they
differ), the seat, the booking reference and the travellers, and **Show Ticket** at
the bottom.
