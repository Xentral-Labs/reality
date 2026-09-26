"""Own the durable state of one installed Reality Local application.

The installation keeps its database, artifacts and identity until the owner erases it.
Moving the application to the Trash never removes data; erasure is a separate confirmed
command that touches exactly one installation directory.
"""

from __future__ import annotations

import argparse
import fcntl
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

SCRIPTS = Path(__file__).resolve().parent
LAYOUT_VERSION = 1
DEFAULT_IDENTIFIER = "ai.runreality.local"
ROLE = "reality_local"
DATABASE = "reality"
CHECKPOINTS_RETAINED = 3
# A quit stops the API, jobs and PostgreSQL; reopening at once must not look like a clash.
REOPEN_WAIT_SECONDS = 60


def _cluster():
    """Load the shared cluster helpers beside this file without a package import."""
    spec = importlib.util.spec_from_file_location(
        "desktop_cluster", SCRIPTS / "cluster.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


cluster = _cluster()
private_socket_directory = cluster.private_socket_directory


def _recovery():
    """Load the durable-generation rules beside this file."""
    spec = importlib.util.spec_from_file_location(
        "desktop_recovery", SCRIPTS / "recovery.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


recovery = _recovery()


def _backup():
    """Load the encrypted backup envelope beside this file."""
    spec = importlib.util.spec_from_file_location(
        "desktop_backup", SCRIPTS / "backup.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


backup = _backup()


class AlreadyRunning(RuntimeError):
    """Another process holds this installation."""


class ErasureInProgress(RuntimeError):
    """An installation is quarantined until native Keychain erasure resolves."""


@dataclass(frozen=True)
class Installation:
    identifier: str
    root: Path
    base: Path
    created: bool


def base_directory(
    identifier: str = DEFAULT_IDENTIFIER, home: Path | None = None
) -> Path:
    home = home or Path.home()
    return home / "Library/Application Support" / identifier


def _private(directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    directory.chmod(0o700)
    return directory


def create(base: Path) -> Installation:
    """Create a new installation and make it the active one."""
    if reconcile_erasure(base) == "quarantined":
        raise ErasureInProgress("A Reality Local erasure is in progress.")
    identifier = str(uuid4())
    root = _private(_private(_private(base) / "installations") / identifier)
    for name in ("data", "artifacts", "backups"):
        _private(root / name)
    (root / "installation.json").write_text(
        json.dumps(
            {
                "installation_id": identifier,
                "layout_version": LAYOUT_VERSION,
                "created_at": datetime.now(UTC).isoformat(),
                "app_version": None,
            },
            indent=2,
        )
        + "\n"
    )
    (base / "current").write_text(identifier + "\n")
    return Installation(identifier, root, base, created=True)


def resolve(base: Path) -> Installation:
    """Return the active installation, creating it on first use."""
    if reconcile_erasure(base) == "quarantined":
        raise ErasureInProgress("A Reality Local erasure is in progress.")
    pointer = _private(base) / "current"
    if pointer.exists():
        identifier = pointer.read_text().strip()
        root = base / "installations" / identifier
        if _owned(root, identifier):
            return Installation(identifier, root, base, created=False)
    return create(base)


def _owned(root: Path, identifier: str) -> bool:
    """A directory is ours only when it carries our own identity record."""
    try:
        if str(UUID(identifier)) != identifier:
            return False
    except (ValueError, AttributeError, TypeError):
        return False
    if not root.is_dir() or root.is_symlink():
        return False
    try:
        recorded = json.loads((root / "installation.json").read_text())
    except (OSError, ValueError):
        return False
    return recorded.get("installation_id") == identifier


def record(root: Path, **values) -> None:
    path = root / "installation.json"
    recorded = json.loads(path.read_text())
    recorded.update(values)
    path.write_text(json.dumps(recorded, indent=2) + "\n")


def recorded_version(root: Path) -> str | None:
    try:
        return json.loads((root / "installation.json").read_text()).get("app_version")
    except (OSError, ValueError):
        return None


@contextmanager
def exclusive(root: Path, wait_seconds: float = 0):
    """Hold this installation for one process; a second start is refused.

    Reopening right after a quit is normal, so a short wait covers the previous
    process finishing its shutdown instead of refusing a legitimate restart.
    """
    handle = os.open(root / "run.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        deadline = time.monotonic() + wait_seconds
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if time.monotonic() >= deadline:
                    raise AlreadyRunning(
                        "Reality Local is already running for this installation."
                    ) from error
                time.sleep(0.2)
        yield root
    finally:
        os.close(handle)


def stale_postmaster(data: Path) -> int | None:
    """Remove a leftover pid file; report a process that is genuinely still alive."""
    marker = data / "postmaster.pid"
    if not marker.exists():
        return None
    try:
        pid = int(marker.read_text().splitlines()[0])
    except (OSError, ValueError, IndexError):
        marker.unlink(missing_ok=True)
        return None
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        marker.unlink(missing_ok=True)
        return None
    except PermissionError:
        return pid
    return pid


def _stop_orphan(postgres: Path, data: Path) -> None:
    """Stop a postmaster left behind by a forced termination of a previous run."""
    import subprocess

    if stale_postmaster(data) is None:
        return
    subprocess.run(
        [
            str(postgres / "pg_ctl"),
            "-D",
            str(data),
            "stop",
            "-m",
            "fast",
            "-w",
            "-t",
            "30",
        ],
        env=cluster.ENVIRONMENT,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if stale_postmaster(data) is not None:
        raise RuntimeError(
            "A previous database process is still running for this installation."
        )


def _stop_owned_generations(postgres: Path, root: Path) -> None:
    """Stop postmasters from any owned generation before journal reconciliation."""
    generations = root / "data-generations"
    if not generations.is_dir():
        return
    for data in generations.iterdir():
        if not data.is_dir() or data.is_symlink():
            continue
        try:
            if str(UUID(data.name)) != data.name:
                continue
        except ValueError:
            continue
        _stop_orphan(postgres, data)


@contextmanager
def _started(postgres: Path, data: Path, root: Path):
    """Run one generation on a fresh private socket and stop it deterministically."""
    _stop_orphan(postgres, data)
    with (
        cluster.private_socket_directory() as socket_directory,
        (root / "postgres.log").open("w+") as log,
    ):
        process = cluster.launch(postgres, data, socket_directory, log)
        try:
            cluster.wait_until_ready(
                postgres, socket_directory, process, log, role=ROLE
            )
            yield socket_directory
        finally:
            cluster.shut_down(process)


def _migrate(runtime: Path, socket_directory: Path, password: str) -> None:
    """Run only current migrations against a staged generation via private stdin."""
    migrated = subprocess.run(
        [
            str(runtime / "python/bin/python3.12"),
            "-I",
            "-B",
            str(SCRIPTS / "migrate-database.py"),
        ],
        input=json.dumps(
            {
                "database_url": cluster.database_url(
                    ROLE, password, socket_directory, DATABASE
                ),
                "core_root": str(runtime / "core"),
            }
        )
        + "\n",
        env=cluster.ENVIRONMENT,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if migrated.returncode:
        detail = migrated.stderr[-4000:].replace(password, "[redacted]").strip()
        raise RuntimeError(f"Staged database migration failed: {detail}")


def _stage_upgrade(
    root: Path,
    runtime: Path,
    postgres: Path,
    password: str,
    archive: Path,
    *,
    installation_id: str,
    source: Path,
    from_version: str,
    to_version: str,
) -> Path:
    """Restore, migrate and validate a sibling generation before activation."""
    manifest_path = archive.with_suffix(archive.suffix + ".json")
    recovery.validate_checkpoint(
        postgres / "pg_restore",
        archive,
        manifest_path,
        installation_id=installation_id,
        generation_id=source.name,
    )
    return _stage_archive(
        root,
        runtime,
        postgres,
        password,
        archive,
        source=source,
        from_version=from_version,
        to_version=to_version,
    )


def _stage_archive(
    root: Path,
    runtime: Path,
    postgres: Path,
    password: str,
    archive: Path,
    *,
    source: Path,
    from_version: str,
    to_version: str,
) -> Path:
    """Restore one admitted archive into a sibling and activate only after validation."""
    recovery.require_staging_space(root, checkpoint_bytes=archive.stat().st_size)
    staged = recovery.begin_stage(
        root,
        source=source.name,
        from_version=from_version,
        to_version=to_version,
    )
    password_file = root / ".stage-password"
    try:
        password_file.write_text(password)
        password_file.chmod(0o600)
        cluster.initialize(postgres, staged, password_file, role=ROLE)
        with _started(postgres, staged, root) as socket_directory:
            cluster.create_database(
                postgres, socket_directory, password, role=ROLE, name=DATABASE
            )
            recovery.record_phase(root, staged.name, "restore")
            cluster.restore(
                postgres,
                socket_directory,
                password,
                role=ROLE,
                database=DATABASE,
                archive=archive,
            )
            recovery.record_phase(root, staged.name, "migration")
            _migrate(runtime, socket_directory, password)
            recovery.record_phase(root, staged.name, "verification")
            revision = cluster.schema_revision(
                postgres,
                socket_directory,
                password,
                role=ROLE,
                database=DATABASE,
            )
        recovery.mark_validated(root, staged.name, schema_revision=revision)
        recovery.activate(root, staged.name)
        return staged
    except Exception:
        recovery.fail_stage(root, staged.name, "staged upgrade failed")
        raise
    finally:
        password_file.unlink(missing_ok=True)


def create_encrypted_backup(
    root: Path,
    postgres: Path,
    socket_directory: Path,
    password: str,
    destination: Path,
    vault_master_key: str,
    *,
    installation_id: str,
    application_version: str,
    schema_revision: str,
) -> dict:
    """Dump the running database and publish only its encrypted backup envelope."""
    plaintext = root / "backups" / f".user-backup-{uuid4()}.dump"
    try:
        cluster.dump(
            postgres,
            socket_directory,
            password,
            role=ROLE,
            database=DATABASE,
            archive=plaintext,
        )
        recovery.validate_database_archive(postgres / "pg_restore", plaintext)
        key = backup.key_from_vault(vault_master_key, installation_id=installation_id)
        return backup.encrypt_archive(
            plaintext,
            destination,
            key,
            installation_id=installation_id,
            application_version=application_version,
            schema_revision=schema_revision,
        )
    finally:
        plaintext.unlink(missing_ok=True)


def restore_encrypted_backup(
    root: Path,
    runtime: Path,
    database_password: str,
    source_backup: Path,
    vault_master_key: str,
    *,
    installation_id: str,
    application_version: str,
    supported_revisions: set[str],
) -> Path:
    """Admit an encrypted backup and restore it through normal staged activation."""
    postgres = runtime / "postgres/bin"
    plaintext = root / "backups" / f".user-restore-{uuid4()}.dump"
    with exclusive(root, wait_seconds=REOPEN_WAIT_SECONDS):
        remove_incomplete_checkpoints(root)
        _stop_owned_generations(postgres, root)
        active = recovery.reconcile(root)
        key = backup.key_from_vault(vault_master_key, installation_id=installation_id)
        try:
            manifest = backup.decrypt_archive(
                source_backup,
                plaintext,
                key,
                expected_installation_id=installation_id,
                supported_revisions=supported_revisions,
            )
            recovery.validate_database_archive(postgres / "pg_restore", plaintext)
            restored = _stage_archive(
                root,
                runtime,
                postgres,
                database_password,
                plaintext,
                source=active,
                from_version=manifest["application_version"],
                to_version=application_version,
            )
            record(root, app_version=application_version)
            return restored
        finally:
            plaintext.unlink(missing_ok=True)


def retain_checkpoints(directory: Path, keep: int = CHECKPOINTS_RETAINED) -> None:
    archives = sorted(directory.glob("*.dump"), key=lambda item: item.stat().st_mtime)
    for archive in archives[: max(len(archives) - keep, 0)]:
        archive.unlink(missing_ok=True)
        archive.with_suffix(archive.suffix + ".json").unlink(missing_ok=True)


def _atomic_installation_json(path: Path, value: dict) -> None:
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


def _erasure_journal(base: Path, identifier: str | None = None) -> dict:
    try:
        value = json.loads((base / "erasure.json").read_text())
    except (OSError, ValueError) as error:
        raise ErasureInProgress("Erasure journal is missing or invalid.") from error
    if (
        set(value) != {"installation_id", "state"}
        or value.get("state") not in {"preparing", "quarantined"}
        or (identifier is not None and value.get("installation_id") != identifier)
    ):
        raise ErasureInProgress("Erasure journal does not match this installation.")
    return value


def reconcile_erasure(base: Path) -> str | None:
    """Resolve only crash states that precede any native Keychain deletion."""
    journal_path = base / "erasure.json"
    if not journal_path.exists():
        return None
    journal = _erasure_journal(base)
    if journal["state"] == "quarantined":
        return "quarantined"
    identifier = journal["installation_id"]
    root = base / "installations" / identifier
    quarantine = base / "erasing" / identifier
    if _owned(root, identifier) and not quarantine.exists():
        journal_path.unlink()
        return None
    if _owned(quarantine, identifier) and not root.exists():
        _atomic_installation_json(
            journal_path, {"installation_id": identifier, "state": "quarantined"}
        )
        return "quarantined"
    raise ErasureInProgress("Erasure crash state is inconsistent.")


def pending_erasure(base: Path) -> str | None:
    """Return the quarantined installation identity without changing its state."""
    if reconcile_erasure(base) != "quarantined":
        return None
    return _erasure_journal(base)["installation_id"]


def active_installation(base: Path) -> Installation:
    """Return an existing active installation without creating a replacement."""
    if reconcile_erasure(base) == "quarantined":
        raise ErasureInProgress("A Reality Local erasure is in progress.")
    try:
        identifier = (base / "current").read_text().strip()
    except OSError as error:
        raise ValueError("No active Reality Local installation exists.") from error
    root = base / "installations" / identifier
    if not _owned(root, identifier):
        raise ValueError("The active Reality Local installation is invalid.")
    return Installation(identifier, root, base, created=False)


def prepare_erasure(base: Path, identifier: str) -> Path:
    """Atomically quarantine one installation before native Keychain deletion."""
    _private(base)
    journal = base / "erasure.json"
    if journal.exists():
        raise ErasureInProgress("A Reality Local erasure is already in progress.")
    root = base / "installations" / identifier
    if not _owned(root, identifier):
        raise ValueError("Not a Reality Local installation directory.")
    quarantine = _private(base / "erasing") / identifier
    if quarantine.exists():
        raise ErasureInProgress("Erasure quarantine already exists.")
    with exclusive(root):
        _atomic_installation_json(
            journal, {"installation_id": identifier, "state": "preparing"}
        )
        os.replace(root, quarantine)
        pointer = base / "current"
        if pointer.exists() and pointer.read_text().strip() == identifier:
            pointer.unlink()
        _atomic_installation_json(
            journal, {"installation_id": identifier, "state": "quarantined"}
        )
    return quarantine


def rollback_erasure(base: Path, identifier: str) -> Path:
    """Restore a quarantine when Keychain deletion did not complete."""
    journal = _erasure_journal(base, identifier)
    if journal["state"] != "quarantined":
        raise ErasureInProgress("Erasure quarantine is not ready for rollback.")
    quarantine = base / "erasing" / identifier
    if not _owned(quarantine, identifier):
        raise ErasureInProgress("Erasure quarantine is missing or foreign.")
    root = _private(base / "installations") / identifier
    if root.exists():
        raise ErasureInProgress("Installation target already exists.")
    os.replace(quarantine, root)
    current = base / "current"
    temporary = base / f".current.{uuid4()}.tmp"
    temporary.write_text(identifier + "\n")
    temporary.chmod(0o600)
    os.replace(temporary, current)
    (base / "erasure.json").unlink()
    return root


def commit_erasure(base: Path, identifier: str) -> Path:
    """Remove a quarantine only after native code verified Keychain deletion."""
    journal = _erasure_journal(base, identifier)
    if journal["state"] != "quarantined":
        raise ErasureInProgress("Erasure quarantine is not ready for commit.")
    quarantine = base / "erasing" / identifier
    if not _owned(quarantine, identifier):
        raise ErasureInProgress("Erasure quarantine is missing or foreign.")
    shutil.rmtree(quarantine)
    (base / "erasure.json").unlink()
    return quarantine


def checkpoint_path(root: Path) -> Path:
    """Return a collision-free checkpoint path that remains human-sortable."""
    backups = _private(root / "backups")
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    return backups / f"{stamp}-{uuid4()}.dump"


def remove_incomplete_checkpoints(root: Path) -> None:
    """Remove only unpublished archives left by a terminated pg_dump."""
    backups = root / "backups"
    if not backups.is_dir():
        return
    for partial in backups.glob(".checkpoint-*.partial"):
        if partial.is_file() and not partial.is_symlink():
            partial.unlink()


def erase(base: Path, identifier: str) -> Path:
    """Remove exactly one installation and nothing beside it."""
    root = base / "installations" / identifier
    if not _owned(root, identifier):
        raise ValueError("Not a Reality Local installation directory.")
    with exclusive(root):
        shutil.rmtree(root)
    pointer = base / "current"
    if pointer.exists() and pointer.read_text().strip() == identifier:
        pointer.unlink()
    return root


def installations(base: Path) -> list[str]:
    directory = base / "installations"
    if not directory.is_dir():
        return []
    return sorted(item.name for item in directory.iterdir() if _owned(item, item.name))


@contextmanager
def running(
    runtime: Path,
    *,
    base: Path | None = None,
    app_version: str = "0.0.0",
    prepared: Installation | None = None,
    database_password: str | None = None,
):
    """Start the durable cluster and yield the environment the product already expects."""
    base = base or base_directory()
    prepared = prepared or resolve(base)
    postgres = runtime / "postgres/bin"
    secret = prepared.root / "secret"
    with exclusive(prepared.root, wait_seconds=REOPEN_WAIT_SECONDS):
        remove_incomplete_checkpoints(prepared.root)
        _stop_owned_generations(postgres, prepared.root)
        data = recovery.reconcile(prepared.root)
        initialized = (data / "PG_VERSION").exists()
        if not initialized:
            password = database_password or cluster.write_password(secret)
            password_file = (
                secret
                if database_password is None
                else prepared.root / ".init-password"
            )
            if database_password is not None:
                password_file.write_text(password)
                password_file.chmod(0o600)
            try:
                cluster.initialize(postgres, data, password_file, role=ROLE)
            finally:
                if database_password is not None:
                    password_file.unlink(missing_ok=True)
        else:
            _stop_orphan(postgres, data)
            password = database_password or secret.read_text().strip()
        previous_version = recorded_version(prepared.root)
        if initialized and previous_version != app_version:
            with _started(postgres, data, prepared.root) as socket_directory:
                revision = cluster.schema_revision(
                    postgres,
                    socket_directory,
                    password,
                    role=ROLE,
                    database=DATABASE,
                )
                archive = checkpoint(
                    prepared.root,
                    postgres,
                    socket_directory,
                    password,
                    installation_id=prepared.identifier,
                    generation_id=data.name,
                    application_version=previous_version or "unknown",
                    schema_revision=revision,
                )
            data = _stage_upgrade(
                prepared.root,
                runtime,
                postgres,
                password,
                archive,
                installation_id=prepared.identifier,
                source=data,
                from_version=previous_version or "unknown",
                to_version=app_version,
            )
        with _started(postgres, data, prepared.root) as socket_directory:
            if not initialized:
                cluster.create_database(
                    postgres, socket_directory, password, role=ROLE, name=DATABASE
                )
            record(prepared.root, app_version=app_version)
            if database_password is not None:
                secret.unlink(missing_ok=True)
            yield (
                dict(
                    cluster.ENVIRONMENT,
                    REALITY_DATABASE_URL=cluster.database_url(
                        ROLE, password, socket_directory, DATABASE
                    ),
                    REALITY_ROOT=str(runtime / "core"),
                    REALITY_ARTIFACT_DIR=str(prepared.root / "artifacts"),
                    REALITY_INSTALLATION_ID=prepared.identifier,
                    REALITY_DATA_DIR=str(data),
                ),
                prepared,
            )


def checkpoint(
    root: Path,
    postgres: Path,
    socket_directory: Path,
    password: str,
    *,
    installation_id: str,
    generation_id: str,
    application_version: str,
    schema_revision: str,
) -> Path:
    """Copy the current database before a changed application version migrates it."""
    backups = _private(root / "backups")
    archive = checkpoint_path(root)
    partial = backups / f".checkpoint-{uuid4()}.partial"
    cluster.dump(
        postgres,
        socket_directory,
        password,
        role=ROLE,
        database=DATABASE,
        archive=partial,
    )
    os.replace(partial, archive)
    directory = os.open(backups, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    recovery.write_checkpoint_manifest(
        archive,
        installation_id=installation_id,
        generation_id=generation_id,
        application_version=application_version,
        schema_revision=schema_revision,
    )
    retain_checkpoints(backups)
    return archive


def _size(root: Path) -> int:
    return sum(item.stat().st_size for item in root.rglob("*") if item.is_file())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--identifier", default=DEFAULT_IDENTIFIER)
    parser.add_argument(
        "--uninstall",
        action="store_true",
        help="Erase the active installation, including its business data",
    )
    parser.add_argument(
        "--yes", action="store_true", help="Skip the typed confirmation"
    )
    arguments = parser.parse_args()
    base = base_directory(arguments.identifier)
    present = installations(base)
    if not present:
        print(f"No Reality Local installation under {base}")
        return
    pointer = base / "current"
    active = pointer.read_text().strip() if pointer.exists() else present[0]
    root = base / "installations" / active
    if not arguments.uninstall:
        print(f"Installation: {active}")
        print(f"Location:     {root}")
        print(f"Size:         {_size(root) / 1_000_000:.1f} MB")
        print(f"Version:      {recorded_version(root) or 'unknown'}")
        print(f"Checkpoints:  {len(list((root / 'backups').glob('*.dump')))}")
        print("\nMoving the application to the Trash keeps this data.")
        print("Run with --uninstall to erase it.")
        return
    print(f"This permanently erases {root}")
    print("Every company, document and setting in this installation is removed.")
    if not arguments.yes and input("Type ERASE to confirm: ").strip() != "ERASE":
        print("Nothing was removed.")
        raise SystemExit(1)
    try:
        erase(base, active)
    except AlreadyRunning:
        raise SystemExit("Quit Reality Local before erasing its data.") from None
    print("Removed. Other installations and unrelated files were not touched.")


if __name__ == "__main__":
    main()
