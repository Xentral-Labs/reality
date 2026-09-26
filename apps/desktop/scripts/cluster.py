"""Start a socket-only PostgreSQL cluster for one desktop installation.

Shared by the disposable qualification harness and the persistent installation, so
both use the same private transport, authentication and shutdown behavior.
"""

from __future__ import annotations

import os
import secrets
import subprocess
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote

# macOS rejects Unix socket paths beyond this length. An Application Support path plus
# an installation identifier exceeds it, so the socket never lives beside the data.
SOCKET_PATH_LIMIT = 104
SOCKET_FILE = ".s.PGSQL.5432"
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"}


def write_password(path: Path) -> str:
    """Create an unguessable cluster password readable only by this account."""
    password = secrets.token_urlsafe(32)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as stream:
        stream.write(password)
    return password


@contextmanager
def private_socket_directory():
    """Yield a private short-path directory for the cluster socket."""
    parent = Path("/private/tmp") if Path("/private/tmp").is_dir() else None
    directory = Path(tempfile.mkdtemp(prefix="rl-", dir=parent))
    try:
        if len(str(directory / SOCKET_FILE).encode()) >= SOCKET_PATH_LIMIT:
            raise RuntimeError("Socket path exceeds the macOS limit")
        yield directory
    finally:
        for item in directory.iterdir():
            item.unlink(missing_ok=True)
        directory.rmdir()


def initialize(postgres: Path, data: Path, password_file: Path, *, role: str) -> None:
    """Create a cluster that answers only on its private socket."""
    initialized = subprocess.run(
        [
            str(postgres / "initdb"),
            "-D",
            str(data),
            "-U",
            role,
            "--auth-local=scram-sha-256",
            "--auth-host=reject",
            f"--pwfile={password_file}",
            "--no-locale",
            "--encoding=UTF8",
        ],
        env=ENVIRONMENT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    if initialized.returncode:
        raise RuntimeError(f"initdb failed: {initialized.stderr}")


def launch(postgres: Path, data: Path, socket_directory: Path, log):
    """Start PostgreSQL without any TCP listener."""
    return subprocess.Popen(
        [
            str(postgres / "postgres"),
            "-D",
            str(data),
            "-h",
            "",
            "-k",
            str(socket_directory),
            "-c",
            "unix_socket_permissions=0700",
            "-c",
            "max_connections=20",
        ],
        env=ENVIRONMENT,
        stdout=log,
        stderr=log,
    )


def wait_until_ready(
    postgres: Path,
    socket_directory: Path,
    process,
    log,
    *,
    role: str,
    seconds: int = 30,
) -> None:
    deadline = time.monotonic() + seconds
    while True:
        if process.poll() is not None:
            log.seek(0)
            raise RuntimeError(f"PostgreSQL exited during startup: {log.read()}")
        ready = subprocess.run(
            [
                str(postgres / "pg_isready"),
                "-h",
                str(socket_directory),
                "-U",
                role,
                "-d",
                "postgres",
            ],
            env=ENVIRONMENT,
            capture_output=True,
            timeout=3,
            check=False,
        )
        if ready.returncode == 0:
            return
        if time.monotonic() >= deadline:
            raise RuntimeError("PostgreSQL readiness timed out")
        time.sleep(0.1)


def database_url(
    role: str, password: str, socket_directory: Path, database: str
) -> str:
    return (
        f"postgresql+psycopg://{role}:{quote(password, safe='')}@/{database}"
        f"?host={quote(str(socket_directory), safe='')}"
    )


def create_database(
    postgres: Path, socket_directory: Path, password: str, *, role: str, name: str
) -> None:
    created = subprocess.run(
        [
            str(postgres / "createdb"),
            "-h",
            str(socket_directory),
            "-U",
            role,
            "-O",
            role,
            name,
        ],
        env=dict(ENVIRONMENT, PGPASSWORD=password),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    if created.returncode:
        raise RuntimeError(created.stderr.replace(password, "[redacted]"))


def dump(
    postgres: Path,
    socket_directory: Path,
    password: str,
    *,
    role: str,
    database: str,
    archive: Path,
) -> None:
    written = subprocess.run(
        [
            str(postgres / "pg_dump"),
            "-h",
            str(socket_directory),
            "-U",
            role,
            "-d",
            database,
            "--format=custom",
            "--compress=0",
            "--file",
            str(archive),
        ],
        env=dict(ENVIRONMENT, PGPASSWORD=password),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if written.returncode:
        archive.unlink(missing_ok=True)
        raise RuntimeError(written.stderr.replace(password, "[redacted]"))


def restore(
    postgres: Path,
    socket_directory: Path,
    password: str,
    *,
    role: str,
    database: str,
    archive: Path,
) -> None:
    """Restore one validated custom-format archive into an empty database."""
    restored = subprocess.run(
        [
            str(postgres / "pg_restore"),
            "-h",
            str(socket_directory),
            "-U",
            role,
            "-d",
            database,
            "--exit-on-error",
            "--no-owner",
            str(archive),
        ],
        env=dict(ENVIRONMENT, PGPASSWORD=password),
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if restored.returncode:
        raise RuntimeError(restored.stderr.replace(password, "[redacted]"))


def schema_revision(
    postgres: Path,
    socket_directory: Path,
    password: str,
    *,
    role: str,
    database: str,
) -> str:
    """Read the authoritative Alembic revision from a running cluster."""
    queried = subprocess.run(
        [
            str(postgres / "psql"),
            "-h",
            str(socket_directory),
            "-U",
            role,
            "-d",
            database,
            "--no-align",
            "--tuples-only",
            "--command",
            "SELECT version_num FROM alembic_version",
        ],
        env=dict(ENVIRONMENT, PGPASSWORD=password),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    revision = queried.stdout.strip()
    if queried.returncode or not revision or "\n" in revision:
        raise RuntimeError(queried.stderr.replace(password, "[redacted]"))
    return revision


def shut_down(process) -> None:
    if process.poll() is None:
        process.terminate()
    try:
        process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)
