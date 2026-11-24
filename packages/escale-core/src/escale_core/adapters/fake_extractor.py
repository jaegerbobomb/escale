"""An extractor that returns canned JSON-LD, for tests and for platforms without one."""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any


class FakeExtractor:
    def __init__(self, elements: list[dict[str, Any]] | Exception) -> None:
        self._elements = elements
        self.calls: list[Path] = []

    async def extract(self, path: Path) -> list[dict[str, Any]]:
        self.calls.append(path)
        if isinstance(self._elements, Exception):
            raise self._elements
        return copy.deepcopy(self._elements)
