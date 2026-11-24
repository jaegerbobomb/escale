"""Application entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

import flet as ft

from escale_flet import demo
from escale_flet.shell import Shell

ASSETS_DIR = Path(__file__).parent / "assets"


async def main(page: ft.Page) -> None:
    if demo.enabled():
        await demo.run(page)
        return
    Shell().mount(page)


def run(argv: list[str] | None = None) -> None:
    """Start the app: a desktop window by default, or a local web server with ``--web``."""
    parser = argparse.ArgumentParser(prog="escale")
    parser.add_argument("--web", action="store_true", help="serve the app over HTTP")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    args = parser.parse_args(argv)
    ft.run(
        main,
        host=args.host if args.web else None,
        port=args.port,
        view=None if args.web else ft.AppView.FLET_APP,
        assets_dir=str(ASSETS_DIR),
        no_cdn=True,
    )
