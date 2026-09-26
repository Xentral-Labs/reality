"""Kill real staged upgrades at restore/migration boundaries and prove recovery."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), SCRIPTS / f"{name}.py"
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


def wait_for(path: Path, process: subprocess.Popen, seconds: int = 120) -> None:
    deadline = time.monotonic() + seconds
    while not path.exists():
        if process.poll() is not None:
            raise RuntimeError(f"Upgrade worker exited early: {process.stderr.read()}")
        if time.monotonic() >= deadline:
            raise RuntimeError(f"Upgrade worker did not reach {path.name}.")
        time.sleep(0.05)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    arguments = parser.parse_args()
    runtime = arguments.runtime.resolve()
    installation = load("installation")
    evidence: dict = {"phases": {}}

    with tempfile.TemporaryDirectory(prefix="reality-upgrade-kill-") as temporary:
        base = Path(temporary)
        with installation.running(runtime, base=base, app_version="0.1.0") as (
            configuration,
            prepared,
        ):
            seeded = probe(runtime, configuration, "seed", "Upgrade Kill Proof")
        evidence["installation_id"] = prepared.identifier
        evidence["tenant_id"] = seeded["tenant_id"]

        try:
            for index, phase in enumerate(("restore", "migration"), start=2):
                version = f"0.{index}.0"
                marker = prepared.root / f"{phase}-ready"
                worker = subprocess.Popen(
                    [
                        sys.executable,
                        str(SCRIPTS / "upgrade-crash-worker.py"),
                        str(runtime),
                        str(base),
                        phase,
                        version,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                wait_for(marker, worker)
                os.kill(worker.pid, signal.SIGKILL)
                worker.wait(timeout=10)
                marker.unlink(missing_ok=True)
                journal_before = json.loads(
                    (prepared.root / "maintenance.json").read_text()
                )
                with installation.running(runtime, base=base, app_version=version) as (
                    configuration,
                    _prepared,
                ):
                    recovered = probe(runtime, configuration, "read")
                evidence["phases"][phase] = {
                    "worker_returncode": worker.returncode,
                    "journal_phase": journal_before.get("phase"),
                    "tenant_preserved": recovered["tenants"][0][0]
                    == seeded["tenant_id"],
                    "migration_revision": recovered["migration_revision"],
                    "tcp_listening": recovered["tcp_listening"],
                }
        finally:
            installation._stop_owned_generations(
                runtime / "postgres/bin", prepared.root
            )

    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
