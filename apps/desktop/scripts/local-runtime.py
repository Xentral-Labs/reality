"""Start the installed product; the persistent installation keeps its data until erased.

Setting REALITY_DESKTOP_DISPOSABLE=1 selects the fresh-test harness from spec 239
instead, which initializes a new cluster and removes it again on exit.
"""

import argparse
import importlib.util
import json
import os
import plistlib
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from uuid import uuid4

SCRIPTS = Path(__file__).resolve().parent
RUNTIME = SCRIPTS.parent / "runtime"
BUNDLE = SCRIPTS.parents[1] / "Info.plist"


def serve(configuration, root):
    python = RUNTIME / "python/bin/python3.12"
    config = {
        "database_url": configuration["REALITY_DATABASE_URL"],
        "core_root": str(RUNTIME / "core"),
        "artifact_root": str(root / "artifacts"),
        "frontend": str(SCRIPTS.parent / "frontend"),
        "installation_id": configuration.get("REALITY_INSTALLATION_ID") or str(uuid4()),
    }
    # -I ignores PYTHON* variables, so -B is what actually keeps the signed bundle clean.
    env = {"PATH": "/usr/bin:/bin"}
    # Separate exclusive preparation process; API startup never performs migrations.
    prepared = subprocess.run(
        [str(python), "-I", "-B", str(SCRIPTS / "local-product.py"), "--prepare"],
        input=json.dumps(config) + "\n",
        text=True,
        env=env,
        capture_output=True,
        timeout=180,
        check=False,
    )
    if prepared.returncode:
        raise RuntimeError("Local database preparation failed.")
    try:
        config["owner_id"] = json.loads(prepared.stdout)["owner_id"]
    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError("Local identity preparation failed.") from error
    roles = []
    for role in ("scheduler", "worker"):
        child = subprocess.Popen(
            [str(python), "-I", "-B", str(SCRIPTS / "local-background.py"), role],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=sys.stderr,
            text=True,
            env=env,
        )
        child.stdin.write(json.dumps(config) + "\n")
        child.stdin.flush()
        roles.append(child)
    process = subprocess.Popen(
        [str(python), "-I", "-B", str(SCRIPTS / "local-product.py")],
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=sys.stderr,
        text=True,
        env=env,
    )
    process.stdin.write(json.dumps(config) + "\n")
    process.stdin.flush()

    stopping = threading.Event()
    stopped = threading.Event()
    stop_lock = threading.Lock()

    def stop_child(child):
        if child.poll() is not None:
            return
        if child.stdin:
            child.stdin.close()
        try:
            child.wait(timeout=30)
        except subprocess.TimeoutExpired:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()

    def stop_all():
        if stopping.is_set():
            stopped.wait(timeout=40)
            return
        with stop_lock:
            if stopping.is_set():
                stopped.wait(timeout=40)
                return
            stopping.set()
            try:
                for child in roles:
                    stop_child(child)
                stop_child(process)
            finally:
                stopped.set()

    def parent_closed():
        sys.stdin.buffer.read()
        stop_all()

    threading.Thread(target=parent_closed, daemon=True).start()
    try:
        while process.poll() is None:
            if not stopping.is_set() and any(
                child.poll() is not None for child in roles
            ):
                raise RuntimeError("Local background process failed.")
            time.sleep(0.2)
        code = process.returncode
        if code:
            raise RuntimeError("Local product process failed.")
        return {"stopped": True}
    finally:
        stop_all()


def load(name):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), SCRIPTS / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
    spec.loader.exec_module(module)
    return module


def bundle():
    """Read the packaged identity; a changed version triggers a checkpoint before migration."""
    try:
        with BUNDLE.open("rb") as stream:
            information = plistlib.load(stream)
        return (
            information.get("CFBundleIdentifier"),
            information.get("CFBundleShortVersionString") or "0.0.0",
        )
    except (OSError, ValueError):
        return None, "0.0.0-development"


def disposable():
    """The native shell clears the environment, so the package marks its own intent."""
    return (
        os.environ.get("REALITY_DESKTOP_DISPOSABLE") == "1"
        or (SCRIPTS / "disposable").exists()
    )


def unsigned_tester_beta():
    """Select file custody only from immutable package metadata, never user input."""
    marker = SCRIPTS / "unsigned-tester-beta"
    return marker.is_file() and marker.read_text().strip() == "unsigned-tester-beta"


def maintenance_arguments(arguments):
    parser = argparse.ArgumentParser(add_help=False)
    operations = parser.add_mutually_exclusive_group()
    operations.add_argument("--backup", type=Path)
    operations.add_argument("--restore", type=Path)
    operations.add_argument("--erase", action="store_true")
    parser.add_argument("--confirm-restore", action="store_true")
    parser.add_argument("--confirm-erasure", action="store_true")
    parsed = parser.parse_args(arguments)
    if parsed.restore and not parsed.confirm_restore:
        parser.error("--restore requires --confirm-restore")
    if parsed.confirm_restore and not parsed.restore:
        parser.error("--confirm-restore requires --restore")
    if parsed.erase and not parsed.confirm_erasure:
        parser.error("--erase requires --confirm-erasure")
    if parsed.confirm_erasure and not parsed.erase:
        parser.error("--confirm-erasure requires --erase")
    return parsed


def erasure_exchange(installation, base, identifier, operation):
    print(
        json.dumps(
            {
                "kind": "keychain_erasure_request",
                "installation_id": identifier,
                "operation": operation,
            }
        ),
        flush=True,
    )
    response = json.loads(sys.stdin.readline(16384))
    if (
        set(response) != {"kind", "installation_id", "state"}
        or response.get("kind") != "keychain_erasure_response"
        or response.get("installation_id") != identifier
        or response.get("state") not in {"present", "missing", "partial"}
    ):
        raise RuntimeError("Invalid native Keychain erasure response.")
    if response["state"] == "present":
        installation.rollback_erasure(base, identifier)
        return "rolled_back"
    if response["state"] == "missing":
        installation.commit_erasure(base, identifier)
        return "erased"
    raise RuntimeError(
        "Keychain erasure is incomplete; filesystem data remains quarantined."
    )


def migrate_beta_custody(beta_custody, prepared):
    values = beta_custody.load_or_create(
        prepared.root,
        prepared.identifier,
        existing_installation=True,
    )
    print(
        json.dumps(
            {
                "kind": "keychain_migration_request",
                "installation_id": prepared.identifier,
                "database_password": values.database_password,
                "vault_master_key": values.vault_master_key,
            }
        ),
        flush=True,
    )
    migration = json.loads(sys.stdin.readline(16384))
    if migration != {
        "kind": "keychain_migration_response",
        "installation_id": prepared.identifier,
        "exact": True,
    }:
        raise RuntimeError("Native Keychain migration did not verify exact values.")
    beta_custody.complete_migration(prepared.root, prepared.identifier, values)
    return values


def supported_revisions(runtime):
    return {
        path.stem
        for path in (runtime / "core/migrations/versions").glob(
            "[0-9][0-9][0-9][0-9]_*.py"
        )
    }


def main():
    if disposable():
        load("runtime-smoke").smoke(RUNTIME, operation=serve)
        return
    installation = load("installation")
    maintenance = maintenance_arguments(sys.argv[1:])
    identifier, version = bundle()
    base = installation.base_directory(identifier or installation.DEFAULT_IDENTIFIER)
    pending = installation.pending_erasure(base)
    if pending:
        outcome = erasure_exchange(installation, base, pending, "inspect")
        print(
            json.dumps(
                {"kind": "operation_result", "operation": "erasure", "state": outcome}
            ),
            flush=True,
        )
        return
    if maintenance.erase:
        prepared = installation.active_installation(base)
        installation.prepare_erasure(base, prepared.identifier)
        outcome = erasure_exchange(installation, base, prepared.identifier, "delete")
        if outcome != "erased":
            raise RuntimeError("Native Keychain erasure did not complete.")
        print(
            json.dumps(
                {"kind": "operation_result", "operation": "erasure", "state": outcome}
            ),
            flush=True,
        )
        return
    prepared = installation.resolve(base)
    legacy_secret = prepared.root / "secret"
    beta_custody = load("beta-custody")
    if unsigned_tester_beta():
        values = beta_custody.load_or_create(
            prepared.root,
            prepared.identifier,
            existing_installation=not prepared.created,
        )
        print(
            json.dumps(
                {
                    "kind": "beta_custody_request",
                    "installation_id": prepared.identifier,
                }
            ),
            flush=True,
        )
        acknowledgement = json.loads(sys.stdin.readline(16384))
        if acknowledgement != {
            "kind": "beta_custody_response",
            "installation_id": prepared.identifier,
        }:
            raise RuntimeError("Invalid native beta custody response.")
        response = {
            "kind": "keychain_response",
            "installation_id": prepared.identifier,
            "database_password": values.database_password,
            "vault_master_key": values.vault_master_key,
        }
    elif (prepared.root / beta_custody.RECORD).exists() or (
        prepared.root / beta_custody.RECORD
    ).is_symlink():
        values = migrate_beta_custody(beta_custody, prepared)
        response = {
            "kind": "keychain_response",
            "installation_id": prepared.identifier,
            "database_password": values.database_password,
            "vault_master_key": values.vault_master_key,
        }
    else:
        print(
            json.dumps(
                {
                    "kind": "keychain_request",
                    "installation_id": prepared.identifier,
                    "legacy_database_password": (
                        legacy_secret.read_text().strip()
                        if legacy_secret.exists()
                        else None
                    ),
                }
            ),
            flush=True,
        )
        response = json.loads(sys.stdin.readline(16384))
    if (
        set(response)
        != {
            "kind",
            "installation_id",
            "database_password",
            "vault_master_key",
        }
        or response.get("kind") != "keychain_response"
    ):
        raise RuntimeError("Invalid native Keychain response.")
    if response["installation_id"] != prepared.identifier:
        raise RuntimeError("Native Keychain response belongs to another installation.")
    try:
        if maintenance.restore:
            restored = installation.restore_encrypted_backup(
                prepared.root,
                RUNTIME,
                response["database_password"],
                maintenance.restore,
                response["vault_master_key"],
                installation_id=prepared.identifier,
                application_version=version,
                supported_revisions=supported_revisions(RUNTIME),
            )
            print(
                json.dumps(
                    {
                        "kind": "operation_result",
                        "operation": "restore",
                        "generation_id": restored.name,
                    }
                ),
                flush=True,
            )
            return
        with installation.running(
            RUNTIME,
            base=base,
            app_version=version,
            prepared=prepared,
            database_password=response["database_password"],
        ) as (
            configuration,
            prepared,
        ):
            if maintenance.backup:
                socket_directory = Path(
                    parse_qs(urlsplit(configuration["REALITY_DATABASE_URL"]).query)[
                        "host"
                    ][0]
                )
                revision = installation.cluster.schema_revision(
                    RUNTIME / "postgres/bin",
                    socket_directory,
                    response["database_password"],
                    role=installation.ROLE,
                    database=installation.DATABASE,
                )
                manifest = installation.create_encrypted_backup(
                    prepared.root,
                    RUNTIME / "postgres/bin",
                    socket_directory,
                    response["database_password"],
                    maintenance.backup,
                    response["vault_master_key"],
                    installation_id=prepared.identifier,
                    application_version=version,
                    schema_revision=revision,
                )
                print(
                    json.dumps(
                        {
                            "kind": "operation_result",
                            "operation": "backup",
                            "archive_bytes": manifest["archive_bytes"],
                        }
                    ),
                    flush=True,
                )
                return
            configuration["vault_master_key"] = response["vault_master_key"]
            serve(configuration, prepared.root)
    except installation.AlreadyRunning as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
