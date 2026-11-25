# Window layout

Escale has three top-level views: **Current** (the trip you are on), **My trips** and
**Statistics**. It opens on **Current**.

| Window width | Where the views are | "Add" |
|---|---|---|
| 550 px and more | a switcher in the middle of the header | button with a menu, right of the header |
| under 550 px | a bar at the bottom of the window | "+" menu, right of the header |

The layout changes as soon as the window is resized; the selected view stays selected.

The theme follows the system's light or dark preference.

A view can be opened directly by its path in the web version: `/trips`, `/statistics`.

**Current** shows the trip in progress, or else the next one: its name, dates and
travellers, then one card per booking in time order. The next one is outlined and says
how long until it leaves. With no trip ahead, the view says so.

In a trip, **Jump to** lists its bookings: a panel on the left of a wide window, a menu
next to the travellers on a medium one, a button opening a sheet on a narrow one. It
scrolls to the booking and highlights it. Clicking a booking opens its detail;
**‹ trip name** comes back to the same place.
