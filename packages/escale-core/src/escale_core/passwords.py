"""Where the app password is kept (S006b): the system keyring, never the settings file.

Without a keyring (no Secret Service running, a phone), the password is kept in memory
until the app quits, and the UI says it will be asked for again.
"""

from __future__ import annotations

from typing import Protocol


class PasswordStore(Protocol):
    async def get(self, account: str) -> str | None: ...

    async def set(self, account: str, password: str) -> bool:
        """Keep the password; ``False`` when it will not outlive the app."""
        ...

    async def delete(self, account: str) -> None: ...


class MemoryPasswords:
    """Passwords in memory; ``lasting`` pretends they outlive the app (a fake keyring)."""

    def __init__(self, lasting: bool = False) -> None:
        self.lasting = lasting
        self.saved: dict[str, str] = {}

    async def get(self, account: str) -> str | None:
        return self.saved.get(account)

    async def set(self, account: str, password: str) -> bool:
        self.saved[account] = password
        return self.lasting

    async def delete(self, account: str) -> None:
        self.saved.pop(account, None)
