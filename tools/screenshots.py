"""Capture the Flet UI for visual review (issue #11, `visual-review` module).

Serves the app with Flet's web client on localhost and drives it with Playwright:
every view in ``VIEWS``, at every width in ``WIDTHS``, light and dark. Each view is
loaded once per colour scheme at the widest width and then resized, so the captures
also exercise the shell's live re-layout.

    uv run python tools/screenshots.py                # -> build/screenshots/
    uv run python tools/screenshots.py --out shots --views current

Needs a Chromium for Playwright: ``uv run playwright install chromium`` once, or point
``--chromium`` (or ``ESCALE_CHROMIUM``) at an existing binary.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

VIEWS: dict[str, str] = {
    "current": "/",
    "trips": "/trips",
    "statistics": "/statistics",
    # Demo routes (ESCALE_DEMO=1): the import sheets on a synthetic ticket.
    "import-found": "/import-found",
    "import-nothing": "/import-nothing",
    "import-phone": "/import-phone",
    # The current trip, 40 minutes before its first train (S010b).
    "trip": "/trip",
    # Jump index: jumped to the museum (S011); a segment's detail (S011).
    "trip-jump": "/trip-jump",
    "trip-detail": "/trip-detail",
    # A flight's detail, with "Share flight" (S016).
    "flight-detail": "/flight-detail",
    # The hotel's detail: address, room, contact, "Manage booking" (S017a).
    "stay-detail": "/stay-detail",
    # The hotel's editor (S017b).
    "stay-editor": "/stay-editor",
    # The preferences: empty, after a refused password, connected (S006b).
    "preferences": "/preferences",
    "preferences-refused": "/preferences-refused",
    "preferences-connected": "/preferences-connected",
    # The first train's ticket, full screen (S015).
    "ticket": "/ticket",
    # The "Add" menu, opened by a click (see CLICKS).
    "add-menu": "/",
}
"""View name -> route. Add a view here when a story adds or changes one."""

CLICKS: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {
    # "Add" is at the start of the header bar (S061): its menu arrow, or the "+" button.
    "add-menu": ((102, 28), (28, 28)),
}
"""View name -> point to click, in px from the top-LEFT corner, before each capture:
(on a window 550 px wide or more, under 550 px)."""

WIDTHS = (1000, 500, 380)
HEIGHT = 720
SCHEMES = ("light", "dark")
SETTLE_S = 1.5
"""Time for Flutter to lay out and paint after a load or a resize."""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


@contextlib.contextmanager
def serve_app(port: int, timeout_s: float = 60) -> Iterator[str]:
    """Run the app as a local web server for the duration of the block."""
    url = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [sys.executable, "-m", "escale_flet", "--web", "--port", str(port)],
        cwd=ROOT,
        env={**os.environ, "ESCALE_DEMO": "1"},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    try:
        deadline = time.monotonic() + timeout_s
        while True:
            if proc.poll() is not None:
                err = proc.stderr.read().decode() if proc.stderr else ""
                raise RuntimeError(f"the app exited before serving:\n{err}")
            try:
                with urllib.request.urlopen(url, timeout=1):
                    break
            except OSError:
                if time.monotonic() > deadline:
                    raise TimeoutError(f"the app did not answer on {url}") from None
                time.sleep(0.3)
        yield url
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def capture(out: Path, views: list[str], chromium: str | None, scale: float) -> list[Path]:
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    with serve_app(_free_port()) as url, sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=chromium)
        try:
            for scheme in SCHEMES:
                for view in views:
                    context = browser.new_context(
                        viewport={"width": WIDTHS[0], "height": HEIGHT},
                        color_scheme=scheme,  # type: ignore[arg-type]
                        device_scale_factor=scale,
                    )
                    page = context.new_page()
                    page.goto(url + VIEWS[view], wait_until="networkidle")
                    page.wait_for_selector("flutter-view", state="attached")
                    time.sleep(SETTLE_S * 2)  # first paint also loads the fonts
                    for width in WIDTHS:
                        page.set_viewport_size({"width": width, "height": HEIGHT})
                        time.sleep(SETTLE_S)
                        if view in CLICKS:
                            page.keyboard.press("Escape")
                            time.sleep(SETTLE_S / 2)
                            wide, narrow = CLICKS[view]
                            x, y = wide if width >= 550 else narrow
                            page.mouse.click(x, y)
                            time.sleep(SETTLE_S)
                        path = out / f"{view}-{width}-{scheme}.png"
                        page.screenshot(path=str(path))
                        written.append(path)
                    context.close()
        finally:
            browser.close()
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=ROOT / "build" / "screenshots")
    parser.add_argument("--views", nargs="+", choices=sorted(VIEWS), default=list(VIEWS))
    parser.add_argument("--chromium", default=os.environ.get("ESCALE_CHROMIUM"))
    parser.add_argument("--scale", type=float, default=2.0, help="device pixel ratio")
    args = parser.parse_args(argv)
    for path in capture(args.out, args.views, args.chromium, args.scale):
        print(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
