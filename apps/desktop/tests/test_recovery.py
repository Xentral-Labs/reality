"""A failed desktop upgrade never changes the active PostgreSQL generation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/recovery.py"
CRASH_WORKER = Path(__file__).resolve().parent / "helpers/recovery_crash_worker.py"


@pytest.fixture
def recovery():
    spec = importlib.util.spec_from_file_location("desktop_recovery", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_fresh_generation_is_private_stable_and_opaque(recovery, tmp_path):
    first = recovery.resolve_active(tmp_path)
    second = recovery.resolve_active(tmp_path)

    assert first == second
    assert first.parent == tmp_path / "data-generations"
    assert first.stat().st_mode & 0o077 == 0
    assert (tmp_path / "current-data").read_text().strip() == first.name


def test_legacy_data_is_adopted_without_copying_or_discarding_bytes(recovery, tmp_path):
    legacy = tmp_path / "data"
    legacy.mkdir()
    (legacy / "PG_VERSION").write_text("17\n")
    (legacy / "business-bytes").write_bytes(b"exact source bytes")

    active = recovery.resolve_active(tmp_path)

    assert not legacy.exists()
    assert (active / "business-bytes").read_bytes() == b"exact source bytes"
    manifest = json.loads((active.parent / f"{active.name}.json").read_text())
    assert manifest["state"] == "active"
    assert manifest["adopted_legacy"] is True


def test_invalid_pointer_never_escapes_the_installation(recovery, tmp_path):
    tmp_path.mkdir(exist_ok=True)
    (tmp_path / "current-data").write_text("../../foreign\n")

    with pytest.raises(recovery.RecoveryError, match="active data pointer"):
        recovery.resolve_active(tmp_path)


def test_failed_stage_keeps_active_generation_and_removes_only_stage(
    recovery, tmp_path
):
    active = recovery.resolve_active(tmp_path)
    (active / "business-bytes").write_bytes(b"old")
    staged = recovery.begin_stage(
        tmp_path, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )
    (staged / "partial").write_bytes(b"incomplete")

    recovery.fail_stage(tmp_path, staged.name, "migration failed")

    assert recovery.resolve_active(tmp_path) == active
    assert (active / "business-bytes").read_bytes() == b"old"
    assert not staged.exists()
    journal = json.loads((tmp_path / "maintenance.json").read_text())
    assert journal["state"] == "failed"
    assert journal["active_generation"] == active.name
    assert "migration failed" not in json.dumps(journal)


def test_only_validated_stage_can_be_activated_atomically(recovery, tmp_path):
    active = recovery.resolve_active(tmp_path)
    staged = recovery.begin_stage(
        tmp_path, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )
    with pytest.raises(recovery.RecoveryError, match="validated"):
        recovery.activate(tmp_path, staged.name)

    recovery.mark_validated(tmp_path, staged.name, schema_revision="0099_example")
    recovery.activate(tmp_path, staged.name)

    assert recovery.resolve_active(tmp_path) == staged
    assert active.is_dir()
    journal = json.loads((tmp_path / "maintenance.json").read_text())
    assert journal["state"] == "complete"
    assert journal["active_generation"] == staged.name


def test_checkpoint_manifest_binds_archive_installation_generation_and_versions(
    recovery, tmp_path, monkeypatch
):
    archive = tmp_path / "checkpoint.dump"
    archive.write_bytes(b"exact dump bytes")
    manifest = recovery.write_checkpoint_manifest(
        archive,
        installation_id="installation-a",
        generation_id="generation-a",
        application_version="0.1.0",
        schema_revision="0099_example",
    )
    monkeypatch.setattr(
        recovery.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, stdout="TABLE DATA public alembic_version\n", stderr=""
        ),
    )

    recovered = recovery.validate_checkpoint(
        tmp_path / "pg_restore",
        archive,
        manifest,
        installation_id="installation-a",
        generation_id="generation-a",
    )

    assert recovered["schema_revision"] == "0099_example"
    archive.write_bytes(b"x" * len(b"exact dump bytes"))
    with pytest.raises(recovery.RecoveryError, match="digest"):
        recovery.validate_checkpoint(
            tmp_path / "pg_restore",
            archive,
            manifest,
            installation_id="installation-a",
            generation_id="generation-a",
        )


def test_checkpoint_validation_rejects_foreign_or_unreadable_archive(
    recovery, tmp_path, monkeypatch
):
    archive = tmp_path / "checkpoint.dump"
    archive.write_bytes(b"dump")
    manifest = recovery.write_checkpoint_manifest(
        archive,
        installation_id="installation-a",
        generation_id="generation-a",
        application_version="0.1.0",
        schema_revision="0099_example",
    )
    with pytest.raises(recovery.RecoveryError, match="another installation"):
        recovery.validate_checkpoint(
            tmp_path / "pg_restore",
            archive,
            manifest,
            installation_id="installation-b",
            generation_id="generation-a",
        )
    monkeypatch.setattr(
        recovery.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 1, stdout="", stderr="corrupt archive"
        ),
    )
    with pytest.raises(recovery.RecoveryError, match="not readable"):
        recovery.validate_checkpoint(
            tmp_path / "pg_restore",
            archive,
            manifest,
            installation_id="installation-a",
            generation_id="generation-a",
        )


def test_staging_space_is_checked_before_work_begins(recovery, tmp_path, monkeypatch):
    usage = recovery.shutil.disk_usage(tmp_path)
    monkeypatch.setattr(
        recovery.shutil,
        "disk_usage",
        lambda _path: usage._replace(free=99),
    )
    with pytest.raises(recovery.RecoveryError, match="free disk space"):
        recovery.require_staging_space(tmp_path, checkpoint_bytes=100)


def test_failed_stage_after_validation_still_preserves_active_data(recovery, tmp_path):
    active = recovery.resolve_active(tmp_path)
    (active / "business-bytes").write_bytes(b"old")
    staged = recovery.begin_stage(
        tmp_path, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )
    recovery.mark_validated(tmp_path, staged.name, schema_revision="0099_example")

    recovery.fail_stage(tmp_path, staged.name, "activation interrupted")

    assert recovery.resolve_active(tmp_path) == active
    assert (active / "business-bytes").read_bytes() == b"old"
    assert not staged.exists()


@pytest.mark.parametrize("staged_state", ["preparing", "validated", "active"])
def test_reconcile_before_pointer_switch_rolls_back_incomplete_stage(
    recovery, tmp_path, staged_state
):
    active = recovery.resolve_active(tmp_path)
    staged = recovery.begin_stage(
        tmp_path, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )
    staged_manifest_path = staged.parent / f"{staged.name}.json"
    staged_manifest = json.loads(staged_manifest_path.read_text())
    staged_manifest["state"] = staged_state
    recovery._atomic_json(staged_manifest_path, staged_manifest)

    recovered = recovery.reconcile(tmp_path)

    assert recovered == active
    assert not staged.exists()
    assert json.loads((tmp_path / "maintenance.json").read_text())["state"] == "failed"


def test_reconcile_after_pointer_switch_completes_activation(recovery, tmp_path):
    active = recovery.resolve_active(tmp_path)
    staged = recovery.begin_stage(
        tmp_path, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )
    recovery.mark_validated(tmp_path, staged.name, schema_revision="0099_example")
    staged_manifest_path = staged.parent / f"{staged.name}.json"
    staged_manifest = json.loads(staged_manifest_path.read_text())
    staged_manifest["state"] = "active"
    recovery._atomic_json(staged_manifest_path, staged_manifest)
    recovery._atomic_pointer(tmp_path, staged.name)

    recovered = recovery.reconcile(tmp_path)

    assert recovered == staged
    assert (
        json.loads((active.parent / f"{active.name}.json").read_text())["state"]
        == "retained"
    )
    journal = json.loads((tmp_path / "maintenance.json").read_text())
    assert journal == {
        "state": "complete",
        "active_generation": staged.name,
        "retained_generation": active.name,
    }


def test_reconcile_rejects_a_journal_that_names_an_unrelated_generation(
    recovery, tmp_path
):
    recovery.resolve_active(tmp_path)
    (tmp_path / "maintenance.json").write_text(
        json.dumps(
            {
                "state": "preparing",
                "active_generation": "00000000-0000-0000-0000-000000000001",
                "staged_generation": "00000000-0000-0000-0000-000000000002",
            }
        )
    )

    with pytest.raises(recovery.RecoveryError, match="journal"):
        recovery.reconcile(tmp_path)


@pytest.mark.parametrize("pointer_was_written", [False, True])
def test_activation_interruption_is_reconciled_from_durable_state(
    recovery, tmp_path, monkeypatch, pointer_was_written
):
    class SimulatedProcessExit(BaseException):
        pass

    active = recovery.resolve_active(tmp_path)
    staged = recovery.begin_stage(
        tmp_path, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )
    recovery.mark_validated(tmp_path, staged.name, schema_revision="0099_example")
    atomic_pointer = recovery._atomic_pointer

    def interrupt(root, identifier):
        if pointer_was_written:
            atomic_pointer(root, identifier)
        raise SimulatedProcessExit

    monkeypatch.setattr(recovery, "_atomic_pointer", interrupt)
    with pytest.raises(SimulatedProcessExit):
        recovery.activate(tmp_path, staged.name)
    monkeypatch.setattr(recovery, "_atomic_pointer", atomic_pointer)

    recovered = recovery.reconcile(tmp_path)

    if pointer_was_written:
        assert recovered == staged
        assert active.is_dir()
    else:
        assert recovered == active
        assert not staged.exists()


@pytest.mark.parametrize(
    ("boundary", "new_generation_wins"),
    [
        ("preparing", False),
        ("restore", False),
        ("migration", False),
        ("verification", False),
        ("validated", False),
        ("before-pointer", False),
        ("after-pointer", True),
    ],
)
def test_hard_process_exit_is_reconciled_at_each_durable_boundary(
    recovery, tmp_path, boundary, new_generation_wins
):
    source = recovery.resolve_active(tmp_path)
    (source / "business-bytes").write_bytes(b"authoritative")

    crashed = subprocess.run(
        [sys.executable, str(CRASH_WORKER), str(tmp_path), boundary],
        capture_output=True,
        timeout=10,
        check=False,
    )

    assert crashed.returncode < 0
    recovered = recovery.reconcile(tmp_path)
    if new_generation_wins:
        assert recovered != source
        assert (recovered / "partial-restore").is_file()
        assert source.is_dir()
    else:
        assert recovered == source
        assert (source / "business-bytes").read_bytes() == b"authoritative"
        assert len([path for path in source.parent.iterdir() if path.is_dir()]) == 1


@pytest.mark.parametrize("phase", ["restore", "migration", "verification"])
def test_upgrade_phase_is_recorded_without_business_values(recovery, tmp_path, phase):
    active = recovery.resolve_active(tmp_path)
    staged = recovery.begin_stage(
        tmp_path, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )

    recovery.record_phase(tmp_path, staged.name, phase)

    journal = json.loads((tmp_path / "maintenance.json").read_text())
    assert journal["phase"] == phase
    assert journal["state"] == "preparing"
    assert "business" not in json.dumps(journal).lower()


def test_upgrade_phase_rejects_unknown_or_noncurrent_stage(recovery, tmp_path):
    active = recovery.resolve_active(tmp_path)
    staged = recovery.begin_stage(
        tmp_path, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )

    with pytest.raises(recovery.RecoveryError, match="phase"):
        recovery.record_phase(tmp_path, staged.name, "upload")
    with pytest.raises(recovery.RecoveryError, match="journal"):
        recovery.record_phase(
            tmp_path, "00000000-0000-0000-0000-000000000001", "restore"
        )
