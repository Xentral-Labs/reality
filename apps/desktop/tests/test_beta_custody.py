"""Unsigned tester custody is exact, private, and never silently replaced."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/beta-custody.py"


@pytest.fixture
def custody():
    spec = importlib.util.spec_from_file_location("desktop_beta_custody", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_first_start_atomically_creates_private_values_and_reuses_them(
    custody, tmp_path
):
    root = tmp_path / "installation"
    root.mkdir()

    first = custody.load_or_create(root, "chosen", existing_installation=False)
    record = root / "beta-custody.json"
    repeated = custody.load_or_create(root, "chosen", existing_installation=True)

    assert repeated == first
    assert len(first.database_password) == 64
    assert len(first.vault_master_key) >= 43
    assert record.stat().st_mode & 0o777 == 0o600
    assert not list(root.glob(".beta-custody.*.tmp"))
    persisted = json.loads(record.read_text())
    assert set(persisted) == {
        "format_version",
        "installation_id",
        "database_password",
        "vault_master_key",
    }


def test_existing_installation_never_gets_replacement_values(custody, tmp_path):
    root = tmp_path / "installation"
    root.mkdir()

    with pytest.raises(custody.CustodyError, match="missing"):
        custody.load_or_create(root, "chosen", existing_installation=True)


@pytest.mark.parametrize("mode", [0o644, 0o400, 0o660])
def test_permissive_or_inexact_permissions_are_rejected(custody, tmp_path, mode):
    root = tmp_path / "installation"
    root.mkdir()
    custody.load_or_create(root, "chosen", existing_installation=False)
    (root / "beta-custody.json").chmod(mode)

    with pytest.raises(custody.CustodyError, match="permissions"):
        custody.load_or_create(root, "chosen", existing_installation=True)


def test_symlink_and_malformed_records_are_rejected(custody, tmp_path):
    root = tmp_path / "installation"
    root.mkdir()
    foreign = tmp_path / "foreign"
    foreign.write_text("not a custody record")
    (root / "beta-custody.json").symlink_to(foreign)

    with pytest.raises(custody.CustodyError, match="regular file"):
        custody.load_or_create(root, "chosen", existing_installation=True)

    (root / "beta-custody.json").unlink()
    (root / "beta-custody.json").write_text("{}")
    (root / "beta-custody.json").chmod(0o600)
    with pytest.raises(custody.CustodyError, match="invalid"):
        custody.load_or_create(root, "chosen", existing_installation=True)


def test_record_is_bound_to_exact_installation(custody, tmp_path):
    root = tmp_path / "installation"
    root.mkdir()
    custody.load_or_create(root, "chosen", existing_installation=False)

    with pytest.raises(custody.CustodyError, match="another installation"):
        custody.load_or_create(root, "different", existing_installation=True)


def test_migration_removes_only_the_unchanged_exact_record(custody, tmp_path):
    root = tmp_path / "installation"
    root.mkdir()
    values = custody.load_or_create(root, "chosen", existing_installation=False)

    custody.complete_migration(root, "chosen", values)

    assert not (root / "beta-custody.json").exists()


def test_migration_refuses_to_remove_changed_values(custody, tmp_path):
    root = tmp_path / "installation"
    root.mkdir()
    values = custody.load_or_create(root, "chosen", existing_installation=False)
    changed = custody.Values(values.database_password, "different-vault-value" * 3)

    with pytest.raises(custody.CustodyError, match="changed"):
        custody.complete_migration(root, "chosen", changed)
    assert (root / "beta-custody.json").exists()
