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
    (frontend / "index.html").write_text("<html><head></head><body></body></html>")
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
    assert (resources / "probe/recovery.py").is_file()
    assert (resources / "probe/backup.py").is_file()
    assert (resources / "probe/migrate-database.py").is_file()
    assert (resources / "probe/cluster.py").is_file()
    assert not (resources / "probe/disposable").exists()
    assert identity(app)["CFBundleIdentifier"] == "ai.runreality.local"
    assert identity(app)["CFBundleName"] == "Reality Local"
    assert "persistent installation" in printed


def test_release_version_is_written_to_both_bundle_version_fields(
    tmp_path, ingredients
):
    app, _ = build(tmp_path, ingredients, "--version", "2.3.4")

    assert identity(app)["CFBundleShortVersionString"] == "2.3.4"
    assert identity(app)["CFBundleVersion"] == "2.3.4"


def test_persistent_package_can_erase_itself(tmp_path, ingredients):
    app, _ = build(tmp_path, ingredients)
    erase = app / "Contents/Resources/uninstall.command"
    assert erase.is_file() and erase.stat().st_mode & 0o111
    command = erase.read_text()
    assert "../MacOS/reality-local" in command
    assert "--erase --confirm-erasure" in command
    assert "installation.py" not in command


def test_fresh_test_harness_keeps_its_own_identity_and_marker(tmp_path, ingredients):
    app, printed = build(tmp_path, ingredients, "--disposable")
    resources = app / "Contents/Resources"
    assert (resources / "probe/disposable").is_file()
    assert not (resources / "uninstall.command").exists()
    assert identity(app)["CFBundleIdentifier"] == "ai.runreality.local.development"
    assert "fresh-test harness" in printed


def test_unsigned_tester_beta_is_explicit_visible_and_keeps_installation_identity(
    tmp_path, ingredients
):
    app, printed = build(
        tmp_path, ingredients, "--unsigned-tester-beta", "--version", "0.2.0"
    )
    resources = app / "Contents/Resources"
    information = identity(app)

    assert information["CFBundleIdentifier"] == "ai.runreality.local"
    assert information["CFBundleName"] == "Reality Local Unsigned Beta"
    assert information["RealityDistributionChannel"] == "unsigned-tester-beta"
    assert information["RealityReleaseLabel"] == "0.2.0-unsigned-beta"
    assert (resources / "probe/unsigned-tester-beta").read_text().strip() == (
        "unsigned-tester-beta"
    )
    assert (resources / "probe/beta-custody.py").is_file()
    guide = (resources / "UNSIGNED-BETA-INSTALL.txt").read_text()
    assert "named testers only" in guide.lower()
    assert "Open" in guide and "Privacy & Security" in guide
    assert (
        '<meta name="reality-distribution-channel" content="unsigned-tester-beta">'
        in (resources / "frontend/index.html").read_text()
    )
    assert "unsigned tester beta" in printed.lower()


def test_normal_package_does_not_claim_to_be_an_unsigned_beta(tmp_path, ingredients):
    app, _ = build(tmp_path, ingredients)
    assert "reality-distribution-channel" not in (
        app / "Contents/Resources/frontend/index.html"
    ).read_text()


def test_disposable_and_unsigned_beta_modes_are_mutually_exclusive(
    tmp_path, ingredients
):
    runtime, frontend, binary = ingredients
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
            str(tmp_path / "invalid.app"),
            "--disposable",
            "--unsigned-tester-beta",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


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
