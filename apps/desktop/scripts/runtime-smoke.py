"""Run the relocated core on a disposable socket-only PostgreSQL cluster.

Uses no existing database, credentials, fixed TCP port, or application configuration.
This is the fresh-test harness; the persistent installation lives in installation.py.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROLE = "desktop_probe"
DATABASE = "postgres"


def _cluster():
    spec = importlib.util.spec_from_file_location(
        "desktop_cluster", SCRIPTS / "cluster.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


cluster = _cluster()


def smoke(
    runtime: Path, *, temporary_parent: Path = Path("/private/tmp"), operation=None
) -> dict:
    python = runtime / "python/bin/python3.12"
    postgres = runtime / "postgres/bin"
    env = cluster.ENVIRONMENT
    with tempfile.TemporaryDirectory(
        prefix="reality-pg-", dir=temporary_parent
    ) as temporary:
        root = Path(temporary)
        os.chmod(root, 0o700)
        socket_dir = root / "s"
        socket_dir.mkdir(mode=0o700)
        data = root / "data"
        password_file = root / "password"
        password = cluster.write_password(password_file)
        cluster.initialize(postgres, data, password_file, role=ROLE)
        password_file.unlink()
        with (root / "postgres.log").open("w+") as log:
            process = cluster.launch(postgres, data, socket_dir, log)
            try:
                cluster.wait_until_ready(postgres, socket_dir, process, log, role=ROLE)
                core_env = dict(
                    env,
                    REALITY_DATABASE_URL=cluster.database_url(
                        ROLE, password, socket_dir, DATABASE
                    ),
                    REALITY_ROOT=str(runtime / "core"),
                    REALITY_ARTIFACT_DIR=str(root / "artifacts"),
                )
                if operation is not None:
                    return operation(core_env, root)
                checked = subprocess.run(
                    [str(python), "-I", "-B", str(SCRIPTS / "smoke-core.py")],
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
                cluster.dump(
                    postgres,
                    socket_dir,
                    password,
                    role=ROLE,
                    database=DATABASE,
                    archive=dump,
                )
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
                cluster.shut_down(process)


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
