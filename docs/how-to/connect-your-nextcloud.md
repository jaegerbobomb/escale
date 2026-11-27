# Connect your Nextcloud

Escale keeps your trips in a calendar of your Nextcloud and your tickets in its files,
so that every device you connect sees the same trips. You need a Nextcloud account; no
other account is involved.

1. In Nextcloud's web interface, open **Settings › Security** and create an **app
   password** for Escale. Use it instead of your own password: you can revoke it there
   at any time without changing your login.
2. In Escale, open the main menu (☰, at the right of the header bar) and choose
   **Preferences**.
3. Fill in **Server** (the address you open Nextcloud at, such as `cloud.example.org`;
   `https://` is added when you leave it out), **Login** and **App password**, then click
   **Connect**, or press Return.

Once the server accepts them, the preferences show **Connected as** your login and the
calendars of your account. Choose the one Escale should use, or click **Create a Trips
calendar** to have Escale create one. The choice is saved at once; there is nothing else
to confirm. Escale also creates an `Escale` folder in your files, for the tickets.

Once a calendar is chosen, Escale writes each of your reservations there as an event,
in the format KDE Itinerary uses, so that KDE Itinerary can import them too. It does so
right away, after each import or edit, when it starts and every 10 minutes while it is
open. Without network, the changes wait on the device and are sent when the server can
be reached again. A reservation with no date at all stays on the device.

It also takes in what changed on the calendar since: reservations added or edited on
your other devices, or by KDE Itinerary, appear, and those whose event was deleted
disappear.

The PDF or image of each ticket you import goes to the `Escale` folder of your files,
as `Escale/documents/<id>/` with a `meta.json` (KDE Itinerary's layout), before the
reservation's event, so that the event never points to a missing file. A document never
changes, so each one is uploaded once, even when you import the same file again on
another device.

If a reservation you changed here was also changed elsewhere before your change
reached the server, the version on the server is kept and a notice says so: "… was
changed on another device; that version is kept." The same goes for a reservation
deleted elsewhere while you were editing it.

If the connection fails, nothing is saved and the preferences say why: the server
refused the login or the app password, the server cannot be reached, or no Nextcloud
answers at that address.

## Where Escale keeps it

- The **app password** goes to the system keyring (GNOME Keyring or KWallet on Linux),
  never to a file. Without a keyring, Escale says so: the password is forgotten when the
  app quits, and you enter it again next time.
- The server, the login and the chosen calendar go to `settings.json` in
  `$XDG_CONFIG_HOME/escale` (usually `~/.config/escale`). This file is per device.

**Disconnect** forgets the app password and the account on this device. Your calendar
and your files on the server are left as they are.
