"""Create and restore a real encrypted desktop backup through staged activation."""

from __future__ import annotations

import argparse
import base64
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

SCRIPTS = Path(__file__).resolve().parent


def load_installation():
    spec = importlib.util.spec_from_file_location(
        "backup_restore_installation", SCRIPTS / "installation.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def probe(runtime: Path, configuration: dict, *arguments: str) -> dict:
    result = subprocess.run(
        [
            str(runtime / "python/bin/python3.12"),
            "-I",
            "-B",
            str(SCRIPTS / "persistence-probe.py"),
            *arguments,
        ],
        env=configuration,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    arguments = parser.parse_args()
    runtime = arguments.runtime.resolve()
    installation = load_installation()
    vault_key = base64.urlsafe_b64encode(os.urandom(32)).decode()

    with tempfile.TemporaryDirectory(prefix="reality-backup-restore-") as temporary:
        base = Path(temporary)
        destination = base / "company.reality-backup"
        with installation.running(runtime, base=base, app_version="0.1.0") as (
            configuration,
            prepared,
        ):
            first = probe(runtime, configuration, "seed", "Backup Restore Proof")
            socket_directory = Path(
                parse_qs(urlsplit(configuration["REALITY_DATABASE_URL"]).query)["host"][
                    0
                ]
            )
            password = (prepared.root / "secret").read_text().strip()
            installation.create_encrypted_backup(
                prepared.root,
                runtime / "postgres/bin",
                socket_directory,
                password,
                destination,
                vault_key,
                installation_id=prepared.identifier,
                application_version="0.1.0",
                schema_revision=first["migration_revision"],
            )
            second = probe(runtime, configuration, "seed", "Must Disappear")

        before_restore = installation.recovery.resolve_active(prepared.root)
        generations_before = {
            path.name
            for path in (prepared.root / "data-generations").iterdir()
            if path.is_dir()
        }
        rejected = {}
        wrong_key = base64.urlsafe_b64encode(os.urandom(32)).decode()
        for label, candidate, candidate_key in (
            ("wrong_key", destination, wrong_key),
            ("corrupt", base / "corrupt.reality-backup", vault_key),
        ):
            if label == "corrupt":
                damaged = bytearray(destination.read_bytes())
                damaged[len(damaged) // 2] ^= 1
                candidate.write_bytes(damaged)
            try:
                installation.restore_encrypted_backup(
                    prepared.root,
                    runtime,
                    password,
                    candidate,
                    candidate_key,
                    installation_id=prepared.identifier,
                    application_version="0.1.0",
                    supported_revisions={first["migration_revision"]},
                )
            except installation.backup.BackupError:
                rejected[label] = True
            else:
                rejected[label] = False
            assert installation.recovery.resolve_active(prepared.root) == before_restore
            assert {
                path.name
                for path in (prepared.root / "data-generations").iterdir()
                if path.is_dir()
            } == generations_before

        restored = installation.restore_encrypted_backup(
            prepared.root,
            runtime,
            password,
            destination,
            vault_key,
            installation_id=prepared.identifier,
            application_version="0.1.0",
            supported_revisions={first["migration_revision"]},
        )
        with installation.running(runtime, base=base, app_version="0.1.0") as (
            configuration,
            _prepared,
        ):
            after = probe(runtime, configuration, "read")

        tenant_ids = {tenant_id for tenant_id, _name in after["tenants"]}
        print(
            json.dumps(
                {
                    "backup_bytes": destination.stat().st_size,
                    "first_tenant_preserved": first["tenant_id"] in tenant_ids,
                    "later_tenant_removed": second["tenant_id"] not in tenant_ids,
                    "generation_changed": restored != before_restore,
                    "source_retained": before_restore.is_dir(),
                    "wrong_key_rejected_unchanged": rejected["wrong_key"],
                    "corrupt_rejected_unchanged": rejected["corrupt"],
                    "migration_revision": after["migration_revision"],
                    "tcp_listening": after["tcp_listening"],
                },
                indent=2,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
