"""Durable PostgreSQL generation state for Reality Local upgrades."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4


class RecoveryError(RuntimeError):
    """The installation's recovery state is unsafe or inconsistent."""


UPGRADE_PHASES = frozenset({"restore", "migration", "verification"})


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def write_checkpoint_manifest(
    archive: Path,
    *,
    installation_id: str,
    generation_id: str,
    application_version: str,
    schema_revision: str,
) -> Path:
    if not archive.is_file() or archive.stat().st_size == 0:
        raise RecoveryError("Checkpoint archive is empty or missing.")
    manifest = archive.with_suffix(archive.suffix + ".json")
    _atomic_json(
        manifest,
        {
            "format_version": 1,
            "installation_id": installation_id,
            "generation_id": generation_id,
            "application_version": application_version,
            "schema_revision": schema_revision,
            "archive_bytes": archive.stat().st_size,
            "archive_sha256": _digest(archive),
        },
    )
    return manifest


def validate_checkpoint(
    pg_restore: Path,
    archive: Path,
    manifest_path: Path,
    *,
    installation_id: str,
    generation_id: str,
) -> dict:
    try:
        manifest = json.loads(manifest_path.read_text())
    except (OSError, ValueError) as error:
        raise RecoveryError("Checkpoint manifest is missing or invalid.") from error
    if manifest.get("format_version") != 1:
        raise RecoveryError("Checkpoint format is unsupported.")
    if manifest.get("installation_id") != installation_id:
        raise RecoveryError("Checkpoint belongs to another installation.")
    if manifest.get("generation_id") != generation_id:
        raise RecoveryError("Checkpoint belongs to another data generation.")
    if not archive.is_file() or manifest.get("archive_bytes") != archive.stat().st_size:
        raise RecoveryError("Checkpoint archive size does not match its manifest.")
    if manifest.get("archive_sha256") != _digest(archive):
        raise RecoveryError("Checkpoint archive digest does not match its manifest.")
    validate_database_archive(pg_restore, archive)
    return manifest


def validate_database_archive(pg_restore: Path, archive: Path) -> None:
    """Require a readable custom archive containing Reality's schema authority."""
    listed = subprocess.run(
        [str(pg_restore), "--list", str(archive)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if listed.returncode or "alembic_version" not in listed.stdout:
        raise RecoveryError("Checkpoint archive is not readable as a Reality database.")


def require_staging_space(root: Path, *, checkpoint_bytes: int) -> None:
    required = max(checkpoint_bytes * 3, 256 * 1024 * 1024)
    if shutil.disk_usage(root).free < required:
        raise RecoveryError("Insufficient free disk space for staged recovery.")


def _private(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o700)
    return directory


def _identifier(value: str) -> str:
    try:
        if str(UUID(value)) != value:
            raise ValueError
    except (TypeError, ValueError, AttributeError) as error:
        raise RecoveryError("Invalid active data pointer.") from error
    return value


def _atomic_json(path: Path, value: dict) -> None:
    temporary = path.with_name(f".{path.name}.{uuid4()}.tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    temporary.chmod(0o600)
    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _atomic_pointer(root: Path, identifier: str) -> None:
    _identifier(identifier)
    pointer = root / "current-data"
    temporary = root / f".current-data.{uuid4()}.tmp"
    temporary.write_text(identifier + "\n")
    temporary.chmod(0o600)
    with temporary.open("rb") as stream:
        os.fsync(stream.fileno())
    os.replace(temporary, pointer)
    directory = os.open(root, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _manifest(directory: Path) -> dict:
    try:
        value = json.loads(_manifest_path(directory).read_text())
    except (OSError, ValueError) as error:
        raise RecoveryError("Data generation has no valid manifest.") from error
    if value.get("generation_id") != directory.name:
        raise RecoveryError("Data generation identity does not match its directory.")
    return value


def _manifest_path(directory: Path) -> Path:
    return directory.parent / f"{directory.name}.json"


def _new_generation(root: Path, *, adopted_legacy: bool = False) -> Path:
    generations = _private(root / "data-generations")
    identifier = str(uuid4())
    directory = _private(generations / identifier)
    _atomic_json(
        _manifest_path(directory),
        {
            "generation_id": identifier,
            "state": "active",
            "adopted_legacy": adopted_legacy,
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    return directory


def resolve_active(root: Path) -> Path:
    """Resolve one owned active generation, adopting Increment 1 storage once."""
    _private(root)
    pointer = root / "current-data"
    if pointer.exists():
        identifier = _identifier(pointer.read_text().strip())
        directory = root / "data-generations" / identifier
        manifest = _manifest(directory)
        if manifest.get("state") != "active":
            raise RecoveryError(
                "The active data pointer names a non-active generation."
            )
        return directory

    legacy = root / "data"
    if legacy.exists():
        generations = _private(root / "data-generations")
        identifier = str(uuid4())
        directory = generations / identifier
        os.replace(legacy, directory)
        directory.chmod(0o700)
        _atomic_json(
            _manifest_path(directory),
            {
                "generation_id": identifier,
                "state": "active",
                "adopted_legacy": True,
                "created_at": datetime.now(UTC).isoformat(),
            },
        )
    else:
        directory = _new_generation(root)
    _atomic_pointer(root, directory.name)
    return directory


def reconcile(root: Path) -> Path:
    """Resolve an interrupted activation from durable pointer and journal state."""
    journal_path = root / "maintenance.json"
    if not journal_path.exists():
        return resolve_active(root)
    try:
        journal = json.loads(journal_path.read_text())
    except (OSError, ValueError) as error:
        raise RecoveryError("Maintenance journal is missing or invalid.") from error
    if journal.get("state") in {"complete", "failed"}:
        return resolve_active(root)
    if journal.get("state") != "preparing":
        raise RecoveryError("Maintenance journal has an unsupported state.")
    try:
        source_id = _identifier(journal["active_generation"])
        staged_id = _identifier(journal["staged_generation"])
        pointer_id = _identifier((root / "current-data").read_text().strip())
        source = root / "data-generations" / source_id
        staged = root / "data-generations" / staged_id
        source_manifest = _manifest(source)
        staged_manifest = _manifest(staged)
    except (KeyError, OSError, RecoveryError) as error:
        raise RecoveryError("Maintenance journal names invalid generations.") from error

    if pointer_id == source_id:
        if source_manifest.get("state") != "active" or staged_manifest.get(
            "state"
        ) not in {"preparing", "validated", "active"}:
            raise RecoveryError("Maintenance journal contradicts generation state.")
        shutil.rmtree(staged)
        _manifest_path(staged).unlink(missing_ok=True)
        _atomic_json(
            journal_path,
            {
                "state": "failed",
                "active_generation": source_id,
                "staged_generation": staged_id,
            },
        )
        return source

    if pointer_id == staged_id:
        if staged_manifest.get("state") != "active" or source_manifest.get(
            "state"
        ) not in {"active", "retained"}:
            raise RecoveryError("Maintenance journal contradicts generation state.")
        source_manifest["state"] = "retained"
        _atomic_json(_manifest_path(source), source_manifest)
        _atomic_json(
            journal_path,
            {
                "state": "complete",
                "active_generation": staged_id,
                "retained_generation": source_id,
            },
        )
        return staged

    raise RecoveryError("Maintenance journal does not match the active pointer.")


def begin_stage(root: Path, *, source: str, from_version: str, to_version: str) -> Path:
    active = resolve_active(root)
    if source != active.name:
        raise RecoveryError("Upgrade source is not the active data generation.")
    identifier = str(uuid4())
    staged = _private(root / "data-generations" / identifier)
    _atomic_json(
        _manifest_path(staged),
        {
            "generation_id": identifier,
            "state": "preparing",
            "source_generation": source,
            "from_version": from_version,
            "to_version": to_version,
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    _atomic_json(
        root / "maintenance.json",
        {
            "operation_id": str(uuid4()),
            "state": "preparing",
            "active_generation": source,
            "staged_generation": identifier,
            "from_version": from_version,
            "to_version": to_version,
        },
    )
    return staged


def record_phase(root: Path, identifier: str, phase: str) -> None:
    """Durably expose a value-free long-running upgrade phase."""
    if phase not in UPGRADE_PHASES:
        raise RecoveryError("Unsupported upgrade phase.")
    try:
        journal_path = root / "maintenance.json"
        journal = json.loads(journal_path.read_text())
    except (OSError, ValueError) as error:
        raise RecoveryError("Maintenance journal is missing or invalid.") from error
    identifier = _identifier(identifier)
    if (
        journal.get("state") != "preparing"
        or journal.get("staged_generation") != identifier
    ):
        raise RecoveryError("Upgrade phase does not match the maintenance journal.")
    journal["phase"] = phase
    _atomic_json(journal_path, journal)


def mark_validated(root: Path, identifier: str, *, schema_revision: str) -> None:
    directory = root / "data-generations" / _identifier(identifier)
    manifest = _manifest(directory)
    if manifest.get("state") != "preparing":
        raise RecoveryError("Only a preparing generation can be validated.")
    manifest.update(state="validated", schema_revision=schema_revision)
    _atomic_json(_manifest_path(directory), manifest)


def activate(root: Path, identifier: str) -> None:
    directory = root / "data-generations" / _identifier(identifier)
    manifest = _manifest(directory)
    if manifest.get("state") != "validated":
        raise RecoveryError("Only a validated generation can become active.")
    previous = resolve_active(root)
    manifest["state"] = "active"
    _atomic_json(_manifest_path(directory), manifest)
    _atomic_pointer(root, identifier)
    previous_manifest = _manifest(previous)
    previous_manifest["state"] = "retained"
    _atomic_json(_manifest_path(previous), previous_manifest)
    _atomic_json(
        root / "maintenance.json",
        {
            "state": "complete",
            "active_generation": identifier,
            "retained_generation": previous.name,
        },
    )


def fail_stage(root: Path, identifier: str, _reason: str) -> None:
    active = resolve_active(root)
    directory = root / "data-generations" / _identifier(identifier)
    manifest = _manifest(directory)
    if manifest.get("state") not in {"preparing", "validated"}:
        raise RecoveryError("Only an incomplete staged generation may be discarded.")
    shutil.rmtree(directory)
    _manifest_path(directory).unlink(missing_ok=True)
    _atomic_json(
        root / "maintenance.json",
        {
            "state": "failed",
            "active_generation": active.name,
            "staged_generation": identifier,
        },
    )
