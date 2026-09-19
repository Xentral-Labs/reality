"""Run the relocated core on a disposable socket-only PostgreSQL cluster.

Uses no existing database, credentials, fixed TCP port, or application configuration.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.parse import quote

SCRIPTS = Path(__file__).resolve().parent


def smoke(
    runtime: Path, *, temporary_parent: Path = Path("/private/tmp"), operation=None
) -> dict:
    python = runtime / "python/bin/python3.12"
    postgres = runtime / "postgres/bin"
    env = {"PATH": "/usr/bin:/bin", "LC_ALL": "C", "PYTHONDONTWRITEBYTECODE": "1"}
    with tempfile.TemporaryDirectory(
        prefix="reality-pg-", dir=temporary_parent
    ) as temporary:
        root = Path(temporary)
        os.chmod(root, 0o700)
        socket_dir = root / "s"
        socket_dir.mkdir(mode=0o700)
        data = root / "data"
        password = secrets.token_urlsafe(32)
        password_file = root / "password"
        descriptor = os.open(password_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(password)
        initialized = subprocess.run(
            [
                str(postgres / "initdb"),
                "-D",
                str(data),
                "-U",
                "desktop_probe",
                "--auth-local=scram-sha-256",
                "--auth-host=reject",
                f"--pwfile={password_file}",
                "--no-locale",
                "--encoding=UTF8",
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        password_file.unlink()
        if initialized.returncode:
            raise RuntimeError(f"initdb failed: {initialized.stderr}")
        with (root / "postgres.log").open("w+") as log:
            process = subprocess.Popen(
                [
                    str(postgres / "postgres"),
                    "-D",
                    str(data),
                    "-h",
                    "",
                    "-k",
                    str(socket_dir),
                    "-c",
                    "unix_socket_permissions=0700",
                    "-c",
                    "max_connections=20",
                ],
                env=env,
                stdout=log,
                stderr=log,
            )
            try:
                deadline = time.monotonic() + 30
                while True:
                    if process.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(
                            f"PostgreSQL exited during startup: {log.read()}"
                        )
                    ready = subprocess.run(
                        [
                            str(postgres / "pg_isready"),
                            "-h",
                            str(socket_dir),
                            "-U",
                            "desktop_probe",
                            "-d",
                            "postgres",
                        ],
                        env=env,
                        capture_output=True,
                        timeout=3,
                        check=False,
                    )
                    if ready.returncode == 0:
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError("PostgreSQL readiness timed out")
                    time.sleep(0.1)
                core_env = dict(
                    env,
                    REALITY_DATABASE_URL=f"postgresql+psycopg://desktop_probe:{quote(password, safe='')}@/postgres?host={quote(str(socket_dir), safe='')}",
                    REALITY_ROOT=str(runtime / "core"),
                    REALITY_ARTIFACT_DIR=str(root / "artifacts"),
                )
                if operation is not None:
                    return operation(core_env, root)
                checked = subprocess.run(
                    [str(python), "-I", str(SCRIPTS / "smoke-core.py")],
                    env=core_env,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    timeout=180,
                    check=False,
                )
                if checked.returncode:
                    # Redact even unexpected library errors before retaining diagnostic evidence.
                    raise RuntimeError(checked.stderr.replace(password, "[redacted]"))
                result = json.loads(checked.stdout)
                dump = root / "smoke.dump"
                backup_env = dict(env, PGPASSWORD=password)
                backup = subprocess.run(
                    [
                        str(postgres / "pg_dump"),
                        "-h",
                        str(socket_dir),
                        "-U",
                        "desktop_probe",
                        "-d",
                        "postgres",
                        "--format=custom",
                        "--compress=0",
                        "--file",
                        str(dump),
                    ],
                    env=backup_env,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    check=False,
                )
                if backup.returncode:
                    raise RuntimeError(backup.stderr.replace(password, "[redacted]"))
                listed = subprocess.run(
                    [str(postgres / "pg_restore"), "--list", str(dump)],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if listed.returncode or "alembic_version" not in listed.stdout:
                    raise RuntimeError(
                        "Bundled dump/restore tools failed the archive smoke"
                    )
                result["dump_archive_readable"] = True
                return result
            finally:
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(smoke(args.runtime.resolve()), indent=2))
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        parser.exit(1, f"Runtime smoke failed: {error}\n")


if __name__ == "__main__":
    main()
