"""Every module has to import, because a lazy import proves nothing until it runs.

Retiring the configured analytics generation left `services/analytics/proposals.py`
importing a function that no longer existed. The whole suite stayed green: that
module is imported from inside the function that prepares a proposal, so nothing
loaded it, and the first thing that did was a person asking the copilot to save a
report.

Importing everything is the cheapest possible check for that, and it is the one
that was missing.
"""

from __future__ import annotations

import importlib
import pkgutil

import reality


def test_every_module_under_reality_imports():
    broken: list[str] = []
    for module in pkgutil.walk_packages(reality.__path__, "reality."):
        try:
            importlib.import_module(module.name)
        except Exception as error:  # noqa: BLE001 — the point is what broke, not its kind
            broken.append(f"{module.name}: {type(error).__name__}: {error}")
    assert not broken, "\n".join(broken)
