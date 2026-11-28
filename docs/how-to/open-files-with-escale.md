# Open files with Escale

On Linux, Escale can be the application that opens tickets: "Open with Escale" in Files,
or double-clicking a ticket attached to an e-mail. It then starts and shows the import
confirmation for that file, as **Import a file…** does
([Import a ticket](import-a-ticket.md)). It knows PDF tickets, Apple Wallet passes
(`.pkpass`), calendar files (`.ics`), KDE Itinerary exports (`.itinerary`), booking
e-mails (`.eml`, `.html`) and pictures (`.png`, `.jpg`).

From a terminal, the same: `escale path/to/ticket.pdf`.

## Until the Linux package installs it

The Linux package will set this up. Meanwhile, with `escale` on your `PATH`, install
the desktop entry and the `.itinerary` file type for your user from a clone of the
repository:

```bash
install -Dm644 packaging/linux/io.github.jaegerbobomb.Escale.desktop \
  ~/.local/share/applications/io.github.jaegerbobomb.Escale.desktop
install -Dm644 packaging/linux/io.github.jaegerbobomb.Escale.xml \
  ~/.local/share/mime/packages/io.github.jaegerbobomb.Escale.xml
update-mime-database ~/.local/share/mime
update-desktop-database ~/.local/share/applications
```

Escale then appears among the applications that can open these files; choose it in
**Open With…**, or make it the default for a type there.

Each file opened this way starts a new Escale window for now.
