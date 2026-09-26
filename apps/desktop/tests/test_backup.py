"""Encrypted desktop backups are admitted before they can affect active data."""

from __future__ import annotations

import base64
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/backup.py"


@pytest.fixture
def backup():
    spec = importlib.util.spec_from_file_location("desktop_backup", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def create_backup(
    backup, tmp_path, *, installation_id="installation-a", revision="0088"
):
    archive = tmp_path / "source.dump"
    archive.write_bytes(b"private business archive\x00" * 100)
    destination = tmp_path / "company.reality-backup"
    key = bytes(range(32))
    manifest = backup.encrypt_archive(
        archive,
        destination,
        key,
        installation_id=installation_id,
        application_version="0.1.0",
        schema_revision=revision,
    )
    return archive, destination, key, manifest


def test_backup_is_versioned_encrypted_and_round_trips_exact_bytes(backup, tmp_path):
    archive, encrypted, key, manifest = create_backup(backup, tmp_path)
    restored = tmp_path / "restored.dump"

    admitted = backup.decrypt_archive(
        encrypted,
        restored,
        key,
        expected_installation_id="installation-a",
        supported_revisions={"0088", "0099"},
    )

    assert restored.read_bytes() == archive.read_bytes()
    assert manifest["format_version"] == 1
    assert admitted == manifest
    assert b"private business archive" not in encrypted.read_bytes()
    assert b"installation-a" not in encrypted.read_bytes()


@pytest.mark.parametrize("damage", ["wrong-key", "ciphertext", "truncated"])
def test_wrong_key_corruption_or_incomplete_backup_never_publishes_plaintext(
    backup, tmp_path, damage
):
    _archive, encrypted, key, _manifest = create_backup(backup, tmp_path)
    restored = tmp_path / "restored.dump"
    if damage == "wrong-key":
        key = b"x" * 32
    elif damage == "ciphertext":
        value = bytearray(encrypted.read_bytes())
        value[len(value) // 2] ^= 1
        encrypted.write_bytes(value)
    else:
        encrypted.write_bytes(encrypted.read_bytes()[:-10])

    with pytest.raises(backup.BackupError):
        backup.decrypt_archive(
            encrypted,
            restored,
            key,
            expected_installation_id="installation-a",
            supported_revisions={"0088", "0099"},
        )

    assert not restored.exists()
    assert not list(tmp_path.glob("*.partial"))


def test_foreign_installation_or_unknown_schema_is_rejected_before_publication(
    backup, tmp_path
):
    _archive, encrypted, key, _manifest = create_backup(
        backup, tmp_path, revision="future-revision"
    )
    restored = tmp_path / "restored.dump"

    with pytest.raises(backup.BackupError, match="installation"):
        backup.decrypt_archive(
            encrypted,
            restored,
            key,
            expected_installation_id="installation-b",
            supported_revisions={"0088", "0099"},
        )
    with pytest.raises(backup.BackupError, match="schema"):
        backup.decrypt_archive(
            encrypted,
            restored,
            key,
            expected_installation_id="installation-a",
            supported_revisions={"0088", "0099"},
        )
    assert not restored.exists()


def test_manifest_is_strict_and_does_not_accept_unexpected_authority(backup, tmp_path):
    expected = {
        "format_version",
        "installation_id",
        "application_version",
        "schema_revision",
        "created_at",
        "archive_bytes",
        "archive_sha256",
    }
    _archive, _encrypted, _key, manifest = create_backup(backup, tmp_path)

    assert set(manifest) == expected
    json.dumps(manifest)


def test_backup_key_is_domain_separated_by_installation(backup):
    vault_key = base64.urlsafe_b64encode(bytes(range(32))).decode()

    first = backup.key_from_vault(vault_key, installation_id="installation-a")
    repeated = backup.key_from_vault(vault_key, installation_id="installation-a")
    second = backup.key_from_vault(vault_key, installation_id="installation-b")

    assert len(first) == 32
    assert first == repeated
    assert first != second
