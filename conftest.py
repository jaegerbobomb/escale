"""Generate the stories' `.feature` files before the tests are collected.

They are build artifacts (gitignored), so a fresh clone gets them on its first
`uv run pytest`.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def pytest_configure() -> None:
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "extract_features.py"),
            "--output-dir=tests/features",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
