"""The package declares whether it keeps data, and ships its own erasure command."""

from __future__ import annotations

import plistlib
import subprocess
import sys
from pathlib import Path

import pytest

DESKTOP = Path(__file__).resolve().parents[1]
SCRIPT = DESKTOP / "scripts/package-preview.py"


@pytest.fixture
def ingredients(tmp_path):
    runtime = tmp_path / "runtime"
    (runtime / "python/bin").mkdir(parents=True)
    (runtime / "python/bin/python3.12").write_text("#!/bin/sh\n")
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<html></html>")
    binary = tmp_path / "reality-local"
    binary.write_text("#!/bin/sh\n")
    binary.chmod(0o755)
    return runtime, frontend, binary


def build(tmp_path, ingredients, *arguments):
    runtime, frontend, binary = ingredients
    output = tmp_path / f"Reality{len(arguments)}.app"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--runtime",
            str(runtime),
            "--binary",
            str(binary),
            "--frontend",
            str(frontend),
            "--output",
            str(output),
            *arguments,
        ],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return output, result.stdout


def identity(app: Path) -> dict:
    with (app / "Contents/Info.plist").open("rb") as stream:
        return plistlib.load(stream)


def test_persistent_package_ships_the_installation_lifecycle(tmp_path, ingredients):
    app, printed = build(tmp_path, ingredients)
    resources = app / "Contents/Resources"
    assert (resources / "probe/installation.py").is_file()
    assert (resources / "probe/cluster.py").is_file()
    assert not (resources / "probe/disposable").exists()
    assert identity(app)["CFBundleIdentifier"] == "ai.runreality.local"
    assert identity(app)["CFBundleName"] == "Reality Local"
    assert "persistent installation" in printed


def test_persistent_package_can_erase_itself(tmp_path, ingredients):
    app, _ = build(tmp_path, ingredients)
    erase = app / "Contents/Resources/uninstall.command"
    assert erase.is_file() and erase.stat().st_mode & 0o111
    assert "--uninstall" in erase.read_text()


def test_fresh_test_harness_keeps_its_own_identity_and_marker(tmp_path, ingredients):
    app, printed = build(tmp_path, ingredients, "--disposable")
    resources = app / "Contents/Resources"
    assert (resources / "probe/disposable").is_file()
    assert not (resources / "uninstall.command").exists()
    assert identity(app)["CFBundleIdentifier"] == "ai.runreality.local.development"
    assert "fresh-test harness" in printed


def test_the_two_builds_never_share_a_data_directory(tmp_path, ingredients):
    persistent, _ = build(tmp_path, ingredients)
    disposable, _ = build(tmp_path, ingredients, "--disposable")
    assert (
        identity(persistent)["CFBundleIdentifier"]
        != identity(disposable)["CFBundleIdentifier"]
    )


def test_the_shell_never_writes_bytecode_into_the_signed_bundle():
    """Bytecode written beside the bundled scripts invalidates the code signature."""
    shell = (DESKTOP / "src-tauri/src/main.rs").read_text()
    assert '"-B"' in shell
    assert '"PYTHONDONTWRITEBYTECODE", "1"' in shell


def test_packaged_scripts_carry_no_bytecode(tmp_path, ingredients):
    app, _ = build(tmp_path, ingredients)
    assert not list(app.rglob("__pycache__"))


def test_every_bundled_interpreter_call_disables_bytecode():
    """`python -I` ignores PYTHONDONTWRITEBYTECODE, so only -B keeps the bundle sealed."""
    for name in ("local-runtime.py", "runtime-smoke.py", "verify-persistence.py"):
        source = (DESKTOP / "scripts" / name).read_text()
        isolated = source.count('"-I"')
        assert isolated, name
        assert (
            source.count('"-I", "-B"') + source.count('"-I",\n            "-B",')
            == isolated
        ), f"{name} starts the bundled interpreter without -B"
