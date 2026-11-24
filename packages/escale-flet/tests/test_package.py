"""The UI package installs with its core dependency and Flet."""

from importlib.metadata import requires

import escale_core
import escale_flet


def test_ui_package_depends_on_core_and_flet() -> None:
    declared = requires("escale-flet") or []

    assert any(req.startswith("escale-core") for req in declared)
    assert any(req.startswith("flet") for req in declared)
    assert escale_core.__name__ == "escale_core"
    assert escale_flet.__name__ == "escale_flet"
