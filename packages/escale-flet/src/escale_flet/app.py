"""Application entry point."""

from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path

import flet as ft

from escale_core.account import Account
from escale_core.adapters.kitinerary_cli import KitineraryCli
from escale_core.adapters.nextcloud_dav import NextcloudDav
from escale_core.adapters.system_keyring import SystemKeyring
from escale_core.documents import Documents
from escale_core.importer import Importer
from escale_core.settings import SettingsFile, default_config_dir
from escale_core.sqlite_store import SqliteReservationStore, default_data_dir
from escale_core.sync import Sync
from escale_flet import demo
from escale_flet.shell import Shell

APP_ID = "io.github.jaegerbobomb.Escale"
"""The application ID: desktop entry, MIME declaration, future Flatpak (ADR-0010)."""
ASSETS_DIR = Path(__file__).parent / "assets"
SYNC_EVERY_S = 600
"""While the app is open, the calendar is synced this often (S008a)."""

log = logging.getLogger(__name__)


async def keep_in_sync(shell: Shell) -> None:
    """At start, then every ``SYNC_EVERY_S``; a failure waits for the next round."""
    while True:
        try:
            await shell.synchronise()
        except Exception:
            log.exception("calendar sync failed")
        await asyncio.sleep(SYNC_EVERY_S)


async def main(page: ft.Page, opened: Path | None = None) -> None:
    """The app; ``opened`` is a file given on the command line ("Open with", S025a)."""
    if demo.enabled():
        await demo.run(page)
        return
    store = SqliteReservationStore(default_data_dir())
    account = Account(
        SettingsFile(default_config_dir() / "settings.json"), SystemKeyring(), NextcloudDav
    )
    await account.restore()
    sync = Sync(store, account)
    shell = Shell(
        importer=Importer(KitineraryCli(), store),
        account=account,
        sync=sync.run,
        documents=Documents(store, account),
    )
    shell.mount(page)
    await shell.refresh()
    page.run_task(keep_in_sync, shell)
    if opened is not None:
        await shell.open_file(opened)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="escale")
    parser.add_argument("--web", action="store_true", help="serve the app over HTTP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument(
        "file", nargs="?", type=Path, help="a ticket or an export to import (S025a)"
    )
    return parser.parse_args(argv)


def run(argv: list[str] | None = None) -> None:
    """Start the app: a desktop window by default, or a local web server with ``--web``;
    with a file, its import confirmation opens first."""
    args = parse_args(argv)
    opened: Path | None = args.file.resolve() if args.file else None

    async def start(page: ft.Page) -> None:
        await main(page, opened)

    ft.run(
        start,
        host=args.host if args.web else None,
        port=args.port,
        view=None if args.web else ft.AppView.FLET_APP,
        assets_dir=str(ASSETS_DIR),
        no_cdn=True,
    )
