"""Release signing declares and verifies Data-Protection-Keychain authority."""

from __future__ import annotations

import importlib.util
import plistlib
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/release-signing.py"


@pytest.fixture
def signing():
    spec = importlib.util.spec_from_file_location("desktop_release_signing", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_release_entitlements_bind_team_bundle_and_private_keychain_group(
    signing, tmp_path
):
    output = tmp_path / "release.entitlements"
    signing.write_entitlements(
        output, team_id="ABCDE12345", bundle_id="ai.runreality.local"
    )

    value = plistlib.loads(output.read_bytes())
    assert value == {
        "com.apple.application-identifier": "ABCDE12345.ai.runreality.local",
        "com.apple.developer.team-identifier": "ABCDE12345",
        "keychain-access-groups": ["ABCDE12345.ai.runreality.local"],
    }
    assert b"get-task-allow" not in output.read_bytes()


@pytest.mark.parametrize("team_id", ["", "TEAM ID", "team-id"])
def test_invalid_team_identity_is_rejected(signing, team_id):
    with pytest.raises(signing.SigningError, match="team ID"):
        signing.entitlement_values(team_id, "ai.runreality.local")


def test_verification_requires_embedded_provisioning_profile(signing, tmp_path):
    app = tmp_path / "Reality Local.app"
    (app / "Contents").mkdir(parents=True)

    with pytest.raises(signing.SigningError, match="profile"):
        signing.verify(app, team_id="ABCDE12345", bundle_id="ai.runreality.local")


def test_nested_macho_files_are_complete_deterministic_and_leaf_first(
    signing, tmp_path
):
    app = tmp_path / "Reality Local.app"
    executable = app / "Contents/MacOS/reality-local"
    library = app / "Contents/Resources/runtime/python/lib/deep.dylib"
    helper = app / "Contents/Resources/runtime/postgres/bin/postgres"
    for path, magic in (
        (executable, b"\xcf\xfa\xed\xfe"),
        (library, b"\xca\xfe\xba\xbe"),
        (helper, b"\xfe\xed\xfa\xcf"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(magic + b"native")
    (app / "Contents/Resources/readme.txt").write_text("not native")

    assert signing.nested_macho_files(app) == [helper, library]


def test_disk_image_qualification_requires_signature_ticket_and_gatekeeper(
    signing, tmp_path, monkeypatch
):
    dmg = tmp_path / "Reality-Local.dmg"
    dmg.write_bytes(b"dmg")
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(signing.subprocess, "run", run)
    signing.verify_dmg(dmg)

    assert [command[0] for command in commands] == [
        "/usr/bin/codesign",
        "/usr/bin/xcrun",
        "/usr/sbin/spctl",
    ]
    assert "context:primary-signature" in commands[-1]


def test_disk_image_qualification_stops_on_a_failed_gate(
    signing, tmp_path, monkeypatch
):
    dmg = tmp_path / "Reality-Local.dmg"
    dmg.write_bytes(b"dmg")

    def run(command, **kwargs):
        return subprocess.CompletedProcess(command, 1)

    monkeypatch.setattr(signing.subprocess, "run", run)
    with pytest.raises(signing.SigningError, match="qualification failed"):
        signing.verify_dmg(dmg)
