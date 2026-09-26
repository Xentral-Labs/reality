"""Native maintenance arguments keep restore explicit and confirmed."""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/local-runtime.py"


@pytest.fixture
def local_runtime():
    spec = importlib.util.spec_from_file_location("desktop_local_runtime", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_backup_is_read_only_and_does_not_require_mutation_confirmation(local_runtime):
    parsed = local_runtime.maintenance_arguments(["--backup", "/tmp/company.backup"])

    assert parsed.backup == Path("/tmp/company.backup")
    assert parsed.restore is None
    assert not parsed.confirm_restore


def test_restore_requires_explicit_confirmation(local_runtime):
    with pytest.raises(SystemExit):
        local_runtime.maintenance_arguments(["--restore", "/tmp/company.backup"])

    parsed = local_runtime.maintenance_arguments(
        ["--restore", "/tmp/company.backup", "--confirm-restore"]
    )
    assert parsed.restore == Path("/tmp/company.backup")
    assert parsed.confirm_restore


def test_backup_and_restore_are_mutually_exclusive(local_runtime):
    with pytest.raises(SystemExit):
        local_runtime.maintenance_arguments(
            [
                "--backup",
                "/tmp/one.backup",
                "--restore",
                "/tmp/two.backup",
                "--confirm-restore",
            ]
        )


def test_erasure_requires_its_exact_confirmation(local_runtime):
    with pytest.raises(SystemExit):
        local_runtime.maintenance_arguments(["--erase"])
    parsed = local_runtime.maintenance_arguments(["--erase", "--confirm-erasure"])
    assert parsed.erase is True
    with pytest.raises(SystemExit):
        local_runtime.maintenance_arguments(["--confirm-erasure"])


@pytest.mark.parametrize(
    ("state", "method", "outcome"),
    [
        ("present", "rollback_erasure", "rolled_back"),
        ("missing", "commit_erasure", "erased"),
    ],
)
def test_erasure_exchange_resolves_only_unambiguous_states(
    local_runtime, monkeypatch, state, method, outcome
):
    calls = []

    class Installation:
        def rollback_erasure(self, base, identifier):
            calls.append(("rollback_erasure", base, identifier))

        def commit_erasure(self, base, identifier):
            calls.append(("commit_erasure", base, identifier))

    monkeypatch.setattr(
        local_runtime.sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "kind": "keychain_erasure_response",
                    "installation_id": "chosen",
                    "state": state,
                }
            )
            + "\n"
        ),
    )
    assert (
        local_runtime.erasure_exchange(
            Installation(), Path("/base"), "chosen", "delete"
        )
        == outcome
    )
    assert calls == [(method, Path("/base"), "chosen")]


def test_partial_keychain_erasure_keeps_filesystem_quarantined(
    local_runtime, monkeypatch
):
    class Installation:
        def rollback_erasure(self, base, identifier):
            raise AssertionError("partial erasure must not roll back")

        def commit_erasure(self, base, identifier):
            raise AssertionError("partial erasure must not commit")

    monkeypatch.setattr(
        local_runtime.sys,
        "stdin",
        io.StringIO(
            '{"kind":"keychain_erasure_response","installation_id":"chosen","state":"partial"}\n'
        ),
    )
    with pytest.raises(RuntimeError, match="remains quarantined"):
        local_runtime.erasure_exchange(
            Installation(), Path("/base"), "chosen", "inspect"
        )


def test_interrupted_keychain_migration_retains_beta_custody(
    local_runtime, monkeypatch, tmp_path
):
    completed = []
    values = SimpleNamespace(database_password="database", vault_master_key="vault")

    class Custody:
        def load_or_create(self, root, identifier, existing_installation):
            assert existing_installation is True
            return values

        def complete_migration(self, root, identifier, expected):
            completed.append(expected)

    monkeypatch.setattr(local_runtime.sys, "stdin", io.StringIO(""))
    prepared = SimpleNamespace(root=tmp_path, identifier="chosen")
    with pytest.raises((RuntimeError, json.JSONDecodeError)):
        local_runtime.migrate_beta_custody(Custody(), prepared)
    assert completed == []


def test_verified_keychain_migration_removes_exact_beta_custody(
    local_runtime, monkeypatch, tmp_path
):
    completed = []
    values = SimpleNamespace(database_password="database", vault_master_key="vault")

    class Custody:
        def load_or_create(self, root, identifier, existing_installation):
            return values

        def complete_migration(self, root, identifier, expected):
            completed.append((root, identifier, expected))

    monkeypatch.setattr(
        local_runtime.sys,
        "stdin",
        io.StringIO(
            '{"kind":"keychain_migration_response","installation_id":"chosen","exact":true}\n'
        ),
    )
    prepared = SimpleNamespace(root=tmp_path, identifier="chosen")
    assert local_runtime.migrate_beta_custody(Custody(), prepared) is values
    assert completed == [(tmp_path, "chosen", values)]


def test_packaged_bundle_identity_is_read_from_contents(local_runtime):
    assert local_runtime.BUNDLE == local_runtime.SCRIPTS.parents[1] / "Info.plist"


def test_unsigned_beta_custody_is_selected_only_by_exact_package_marker(
    local_runtime, monkeypatch, tmp_path
):
    monkeypatch.setattr(local_runtime, "SCRIPTS", tmp_path)
    assert local_runtime.unsigned_tester_beta() is False
    (tmp_path / "unsigned-tester-beta").write_text("other\n")
    assert local_runtime.unsigned_tester_beta() is False
    (tmp_path / "unsigned-tester-beta").write_text("unsigned-tester-beta\n")
    assert local_runtime.unsigned_tester_beta() is True
