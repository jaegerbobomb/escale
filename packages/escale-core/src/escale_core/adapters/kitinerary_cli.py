"""Run KDE's ``kitinerary-extractor`` on a file and read its JSON-LD (ADR-0003)."""

from __future__ import annotations

import asyncio
import json
import os
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Any

BINARY = "kitinerary-extractor"

DISTRIBUTION_PATHS: tuple[Path, ...] = (
    Path("/usr/lib/x86_64-linux-gnu/libexec/kf6") / BINARY,
    Path("/usr/lib/x86_64-linux-gnu/libexec/kf5") / BINARY,
    Path("/usr/lib/aarch64-linux-gnu/libexec/kf6") / BINARY,
    Path("/usr/lib/aarch64-linux-gnu/libexec/kf5") / BINARY,
    Path("/usr/libexec/kf6") / BINARY,
    Path("/usr/libexec/kf5") / BINARY,
)
"""Where Linux distributions install the extractor, outside ``PATH``."""

DEFAULT_TIMEOUT_S = 30.0


class ExtractorNotFoundError(Exception):
    """No ``kitinerary-extractor`` binary could be found."""


class ExtractorError(Exception):
    """The extractor ran but did not produce a usable result."""


def _executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def find_extractor(
    configured: Path | None = None,
    search_path: str | None = None,
    fallbacks: Sequence[Path] = DISTRIBUTION_PATHS,
) -> Path | None:
    """The binary to run: on ``PATH`` first, then ``configured``, then distribution paths."""
    on_path = shutil.which(BINARY, path=search_path)
    if on_path is not None:
        return Path(on_path)
    for candidate in (configured, *fallbacks):
        if candidate is not None and _executable(candidate):
            return candidate
    return None


class KitineraryCli:
    """Extractor adapter around the ``kitinerary-extractor`` command."""

    def __init__(
        self,
        configured: Path | None = None,
        *,
        search_path: str | None = None,
        fallbacks: Sequence[Path] = DISTRIBUTION_PATHS,
        timeout: float = DEFAULT_TIMEOUT_S,
    ) -> None:
        self._configured = configured
        self._search_path = search_path
        self._fallbacks = fallbacks
        self._timeout = timeout

    async def extract(self, path: Path) -> list[dict[str, Any]]:
        binary = find_extractor(self._configured, self._search_path, self._fallbacks)
        if binary is None:
            raise ExtractorNotFoundError(f"{BINARY} is not installed")
        process = await asyncio.create_subprocess_exec(
            str(binary),
            str(path),
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), self._timeout)
        except TimeoutError:
            process.kill()
            await process.wait()
            raise ExtractorError(f"{BINARY} timed out after {self._timeout:g} s") from None
        if process.returncode != 0:
            detail = stderr.decode(errors="replace").strip()
            raise ExtractorError(f"{BINARY} failed ({process.returncode}): {detail}")
        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as e:
            raise ExtractorError(f"{BINARY} printed invalid JSON: {e}") from None
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ExtractorError(f"{BINARY} did not print a JSON array of objects")
        return data
