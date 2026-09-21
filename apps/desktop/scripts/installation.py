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
import sys
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


class AlreadyRunning(RuntimeError):
    """Another process holds this installation."""


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
def exclusive(root: Path):
    """Hold this installation for one process; a second start is refused."""
    handle = os.open(root / "run.lock", os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise AlreadyRunning(
                "Reality Local is already running for this installation."
            ) from error
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


def retain_checkpoints(directory: Path, keep: int = CHECKPOINTS_RETAINED) -> None:
    archives = sorted(directory.glob("*.dump"), key=lambda item: item.stat().st_mtime)
    for archive in archives[: max(len(archives) - keep, 0)]:
        archive.unlink(missing_ok=True)


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
def running(runtime: Path, *, base: Path | None = None, app_version: str = "0.0.0"):
    """Start the durable cluster and yield the environment the product already expects."""
    base = base or base_directory()
    prepared = resolve(base)
    postgres = runtime / "postgres/bin"
    data = prepared.root / "data"
    secret = prepared.root / "secret"
    with exclusive(prepared.root):
        initialized = (data / "PG_VERSION").exists()
        if not initialized:
            if secret.exists():
                secret.unlink()
            password = cluster.write_password(secret)
            cluster.initialize(postgres, data, secret, role=ROLE)
        else:
            _stop_orphan(postgres, data)
            password = secret.read_text().strip()
        with (
            cluster.private_socket_directory() as socket_directory,
            (prepared.root / "postgres.log").open("w+") as log,
        ):
            process = cluster.launch(postgres, data, socket_directory, log)
            try:
                cluster.wait_until_ready(
                    postgres, socket_directory, process, log, role=ROLE
                )
                if not initialized:
                    cluster.create_database(
                        postgres, socket_directory, password, role=ROLE, name=DATABASE
                    )
                elif recorded_version(prepared.root) != app_version:
                    checkpoint(prepared.root, postgres, socket_directory, password)
                record(prepared.root, app_version=app_version)
                yield (
                    dict(
                        cluster.ENVIRONMENT,
                        REALITY_DATABASE_URL=cluster.database_url(
                            ROLE, password, socket_directory, DATABASE
                        ),
                        REALITY_ROOT=str(runtime / "core"),
                        REALITY_ARTIFACT_DIR=str(prepared.root / "artifacts"),
                        REALITY_INSTALLATION_ID=prepared.identifier,
                    ),
                    prepared,
                )
            finally:
                cluster.shut_down(process)


def checkpoint(
    root: Path, postgres: Path, socket_directory: Path, password: str
) -> Path:
    """Copy the current database before a changed application version migrates it."""
    backups = _private(root / "backups")
    stamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S")
    archive = backups / f"{stamp}.dump"
    cluster.dump(
        postgres,
        socket_directory,
        password,
        role=ROLE,
        database=DATABASE,
        archive=archive,
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
