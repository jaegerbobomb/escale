"""The core never imports Flet (ADR-0002, story S001).

Two independent checks, because each one alone can be fooled:

- the *runtime* check imports every module of the package in a clean interpreter and
  looks at ``sys.modules``: it catches imports reached through a third-party module;
- the *static* check reads the sources: it catches an import hidden inside a function
  body (lazy import) that the runtime check never executes.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import escale_core

FORBIDDEN = "flet"

# Runs in a fresh interpreter so that modules already loaded by pytest (or by the UI
# package's own tests) cannot hide or fake a violation.
_RUNTIME_PROBE = textwrap.dedent(
    """
    import importlib, json, pkgutil, sys

    forbidden = sys.argv[2]

    def leaked():
        return [m for m in sys.modules if m == forbidden or m.startswith(forbidden + ".")]

    def purge():
        for name in leaked():
            del sys.modules[name]

    offenders = []
    package = importlib.import_module(sys.argv[1])
    if leaked():
        offenders.append(package.__name__)
        purge()
    for info in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        importlib.import_module(info.name)
        if leaked():
            offenders.append(info.name)
            purge()
    print(json.dumps(offenders))
    """
)


def _is_forbidden(module: str) -> bool:
    return module == FORBIDDEN or module.startswith(FORBIDDEN + ".")


def runtime_violations(package: str, extra_path: Path | None = None) -> list[str]:
    """Import every module of ``package`` in a subprocess; return those that load Flet."""
    env = dict(os.environ)
    if extra_path is not None:
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (str(extra_path), env.get("PYTHONPATH", "")) if p
        )
    result = subprocess.run(
        [sys.executable, "-c", _RUNTIME_PROBE, package, FORBIDDEN],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    offenders: list[str] = json.loads(result.stdout)
    return offenders


def _forbidden_imports(tree: ast.AST) -> list[int]:
    lines: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(_is_forbidden(alias.name) for alias in node.names):
                lines.append(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module and _is_forbidden(node.module):
                lines.append(node.lineno)
        elif isinstance(node, ast.Call) and node.args:
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            first = node.args[0]
            if (
                name in {"import_module", "__import__"}
                and isinstance(first, ast.Constant)
                and isinstance(first.value, str)
                and _is_forbidden(first.value)
            ):
                lines.append(node.lineno)
    return sorted(lines)


def static_violations(package_dir: Path) -> list[str]:
    """Scan the sources of the package in ``package_dir``; return ``module:line`` hits."""
    root = package_dir.parent
    hits: list[str] = []
    for path in sorted(package_dir.rglob("*.py")):
        parts = list(path.relative_to(root).with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        module = ".".join(parts)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        hits.extend(f"{module}:{line}" for line in _forbidden_imports(tree))
    return hits


CORE_DIR = Path(escale_core.__file__).parent


def test_core_does_not_load_flet_at_runtime() -> None:
    assert runtime_violations("escale_core") == []


def test_core_sources_do_not_import_flet() -> None:
    assert static_violations(CORE_DIR) == []


# --- The checks themselves: a violation must fail and name the module. ---


def _write(base: Path, relative: str, content: str) -> None:
    path = base / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def test_runtime_check_names_the_module_that_imports_flet(tmp_path: Path) -> None:
    _write(tmp_path, "flet/__init__.py", "")  # stand-in, so the probe never needs the real one
    _write(tmp_path, "fakecore/__init__.py", "")
    _write(tmp_path, "fakecore/clean.py", "import json\n")
    _write(tmp_path, "fakecore/services/__init__.py", "")
    _write(tmp_path, "fakecore/services/ui.py", "import flet\n")
    _write(tmp_path, "fakecore/uses_ui.py", "from fakecore.services import ui\n")

    # uses_ui only reaches Flet through services.ui, which is the module to blame.
    assert runtime_violations("fakecore", extra_path=tmp_path) == ["fakecore.services.ui"]


def test_static_check_finds_lazy_and_dynamic_imports(tmp_path: Path) -> None:
    _write(tmp_path, "fakecore/__init__.py", "")
    _write(tmp_path, "fakecore/clean.py", "from . import flet_like\nimport fletcher\n")
    _write(
        tmp_path,
        "fakecore/lazy.py",
        """
        def show() -> None:
            from flet.controls import Text
        """,
    )
    _write(
        tmp_path,
        "fakecore/dynamic.py",
        """
        import importlib

        ui = importlib.import_module("flet")
        """,
    )

    assert static_violations(tmp_path / "fakecore") == ["fakecore.dynamic:4", "fakecore.lazy:3"]
