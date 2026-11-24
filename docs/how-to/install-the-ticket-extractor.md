# Install the ticket extractor (Linux)

Escale reads ticket files with KDE's `kitinerary-extractor`, the engine behind KDE
Itinerary. Until the Linux package ships its own copy (issue #5), install your
distribution's:

| Distribution | Command |
|---|---|
| Debian, Ubuntu | `sudo apt install libkpim5itinerary5` |

Escale looks for the extractor in this order:

1. `kitinerary-extractor` on your `PATH`;
2. where distributions install it: `/usr/lib/<arch>/libexec/kf6/` or `kf5/`,
   `/usr/libexec/kf6/` or `kf5/`.

Without it, importing a file says that the extractor is not installed; nothing else is
affected. Phones do not extract tickets: they receive them through the sync.
