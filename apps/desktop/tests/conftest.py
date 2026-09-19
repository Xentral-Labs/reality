from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

DESKTOP = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def probe_binary(tmp_path_factory):
    target = tmp_path_factory.mktemp("desktop-cargo")
    env = dict(os.environ, CARGO_TARGET_DIR=str(target))
    clt = Path("/Library/Developer/CommandLineTools")
    if clt.is_dir():
        env["DEVELOPER_DIR"] = str(clt)
    result = subprocess.run(
        check=False,
        args=[
            "cargo",
            "build",
            "--offline",
            "--manifest-path",
            str(DESKTOP / "spike/Cargo.toml"),
        ],
        env=env,
        text=True,
        capture_output=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stderr
    return target / "debug/reality-desktop-port-probe"
