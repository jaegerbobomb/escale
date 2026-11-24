# Capture screenshots of the app

Every pull request that adds or changes a screen is reviewed from screenshots: each view
at 1000, 500 and 380 px wide, light and dark.

## Capture them locally

```bash
uv sync --all-packages
uv run playwright install chromium      # once
uv run python tools/screenshots.py
```

The images land in `build/screenshots/` (gitignored), named
`<view>-<width>-<scheme>.png`. To capture only some views:

```bash
uv run python tools/screenshots.py --views current trips --out /tmp/shots
```

If a Chromium is already installed elsewhere, point the tool at it instead of
installing one: `--chromium /path/to/chrome`, or the `ESCALE_CHROMIUM` variable.

## Get them from CI

The `Quality` workflow runs the same tool on every pull request and attaches the
images as the `screenshots` artifact of the run.

## Add a view

A story that adds a view adds it to `VIEWS` in `tools/screenshots.py`, with the route
that opens it. Views are opened by route because the UI is drawn on a canvas: there is
no DOM to click through.

## How it works

`tools/screenshots.py` serves the app with Flet's web client on localhost
(`python -m escale_flet --web`) and drives it with Playwright. Each view is loaded at
1000 px and then resized to 500 and 380 px, so the captures also exercise the live
re-layout. Light and dark come from the browser's `prefers-color-scheme`, which Flet
reports as the platform brightness.

The web client renders with the same Flutter engine as the desktop and mobile apps;
small differences with them (text rendering, scrollbars) are possible. Flet's own `flet.testing`
can take screenshots inside a real Flutter app; it needs the Flutter SDK, so it is kept
for later if the web captures stop being enough.
