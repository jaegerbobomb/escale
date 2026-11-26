"""The device's settings file (S006b): per device, never synced, never a secret.

A JSON file in ``$XDG_CONFIG_HOME/escale``. Each feature owns one key of it and leaves
the others untouched, so that settings added by later stories survive an older save.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

_ACCOUNT = "nextcloud"


def default_config_dir() -> Path:
    """``$XDG_CONFIG_HOME/escale``, or ``~/.config/escale``."""
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "escale"


@dataclass(frozen=True)
class AccountSettings:
    """The Nextcloud account, without its password (that goes to the keyring)."""

    url: str = ""
    login: str = ""
    calendar: str = ""
    """The chosen calendar's URL; empty until the user picks one."""


class SettingsFile:
    def __init__(self, path: Path) -> None:
        self.path = path

    def _read(self) -> dict[str, Any]:
        try:
            data = json.loads(self.path.read_text())
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def account(self) -> AccountSettings:
        saved = self._read().get(_ACCOUNT)
        if not isinstance(saved, dict):
            return AccountSettings()
        return AccountSettings(
            **{k: v for k, v in saved.items() if k in AccountSettings.__dataclass_fields__}
        )

    def save_account(self, account: AccountSettings | None) -> None:
        """Write the account, or remove it (``None``), keeping every other setting."""
        data = self._read()
        if account is None:
            data.pop(_ACCOUNT, None)
        else:
            data[_ACCOUNT] = asdict(account)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2) + "\n")
        temporary.replace(self.path)
