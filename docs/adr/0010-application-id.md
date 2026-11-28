# ADR-0010 — Application ID `io.github.jaegerbobomb.Escale`

- **Status**: accepted
- **Date**: 2026-11-28
- **Deciders**: project maintainer
- **Related stories**: S025a, S057

## Context

The desktop entry of S025a ("Open with Escale") needs a reverse-DNS application ID, the
name of its `.desktop` file and of its icon. The same ID becomes the Flatpak ID of the
Linux package (S057), the D-Bus name, and the key of the user's settings on some
desktops; changing it later breaks installs and settings.

## Decision

The application ID is `io.github.jaegerbobomb.Escale`, from the repository's GitHub
home, as Flathub allows for apps hosted on GitHub. It is `APP_ID` in
`escale_flet.app`; the files under `packaging/linux/` are named after it.

## Consequences

**Positive**
- No domain to buy or keep; the ID follows where the code lives.

**Costs / risks**
- If the repository moves to another owner or forge, the ID stays as it is (changing it
  would cost the users their installs); it then no longer matches the address.

## Rejected alternatives

- **A domain of the project's own**: none exists yet.
