"""Create data with a prior bundled runtime and upgrade it with the current runtime."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def load_installation():
    spec = importlib.util.spec_from_file_location(
        "prior_runtime_installation", SCRIPTS / "installation.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(runtime: Path, configuration: dict, script: str, *arguments: str) -> dict:
    result = subprocess.run(
        [
            str(runtime / "python/bin/python3.12"),
            "-I",
            "-B",
            str(SCRIPTS / script),
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
    parser.add_argument("--prior-runtime", type=Path, required=True)
    parser.add_argument("--current-runtime", type=Path, required=True)
    arguments = parser.parse_args()
    prior = arguments.prior_runtime.resolve()
    current = arguments.current_runtime.resolve()
    installation = load_installation()

    with tempfile.TemporaryDirectory(prefix="reality-prior-upgrade-") as temporary:
        base = Path(temporary)
        with installation.running(prior, base=base, app_version="0.1.0") as (
            configuration,
            prepared,
        ):
            seeded = run(
                prior,
                configuration,
                "legacy-fixture-probe.py",
                "Prior Runtime Upgrade Proof",
            )
            source_generation = Path(configuration["REALITY_DATA_DIR"]).name

        with installation.running(current, base=base, app_version="0.2.0") as (
            configuration,
            _prepared,
        ):
            upgraded = run(current, configuration, "persistence-probe.py", "read")
            active_generation = Path(configuration["REALITY_DATA_DIR"]).name

        evidence = {
            "installation_id": prepared.identifier,
            "prior_revision": seeded["migration_revision"],
            "current_revision": upgraded["migration_revision"],
            "tenant_id": seeded["tenant_id"],
            "tenant_preserved": any(
                tenant_id == seeded["tenant_id"]
                for tenant_id, _name in upgraded["tenants"]
            ),
            "source_generation": source_generation,
            "active_generation": active_generation,
            "generation_changed": source_generation != active_generation,
            "source_retained": (
                prepared.root / "data-generations" / source_generation
            ).is_dir(),
            "checkpoint_count": len(list((prepared.root / "backups").glob("*.dump"))),
            "tcp_listening": upgraded["tcp_listening"],
        }
        print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
