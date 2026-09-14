from __future__ import annotations

from importlib.resources import files

from reality.db.core import ROOT


def config_text(name: str) -> str:
    """Read trusted application configuration in source and installed layouts."""
    source_path = ROOT / "config" / name
    if source_path.is_file():
        return source_path.read_text(encoding="utf-8")
    return files("reality").joinpath("config", name).read_text(encoding="utf-8")
