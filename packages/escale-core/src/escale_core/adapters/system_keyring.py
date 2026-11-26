"""The system keyring through the ``keyring`` library (S006b).

On Linux it talks to the Secret Service (GNOME Keyring, KWallet). When there is none,
``keyring`` falls back to a backend that refuses everything; the password then stays in
memory only. A keyring that stores in plain text is never installed by Escale.
"""

from __future__ import annotations

import asyncio
import contextlib

import keyring
from keyring.errors import KeyringError

SERVICE = "Escale Nextcloud"


class SystemKeyring:
    def __init__(self) -> None:
        self._memory: dict[str, str] = {}

    async def get(self, account: str) -> str | None:
        if account in self._memory:
            return self._memory[account]
        try:
            return await asyncio.to_thread(keyring.get_password, SERVICE, account)
        except KeyringError:
            return None

    async def set(self, account: str, password: str) -> bool:
        try:
            await asyncio.to_thread(keyring.set_password, SERVICE, account, password)
        except KeyringError:
            self._memory[account] = password
            return False
        return True

    async def delete(self, account: str) -> None:
        self._memory.pop(account, None)
        with contextlib.suppress(KeyringError):  # not there, or no keyring
            await asyncio.to_thread(keyring.delete_password, SERVICE, account)
