"""Prove that an installed application keeps its data until it is explicitly erased.

Runs the real installation lifecycle against a built runtime: create data, stop, start
again, confirm the same records, refuse a second start, checkpoint a version change and
erase exactly one installation.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(
        name.replace("-", "_"), SCRIPTS / f"{name}.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(spec.name, module)
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
    parser.add_argument(
        "--base",
        type=Path,
        help="Installation base directory; a temporary one is used by default",
    )
    arguments = parser.parse_args()
    installation = load("installation")
    runtime = arguments.runtime.resolve()
    temporary = None
    if arguments.base:
        base = arguments.base
    else:
        temporary = tempfile.TemporaryDirectory(prefix="reality-base-")
        base = Path(temporary.name)
    evidence: dict = {"base": str(base)}
    try:
        with installation.running(runtime, base=base, app_version="0.1.0") as (
            configuration,
            prepared,
        ):
            evidence["installation_id"] = prepared.identifier
            evidence["first_start"] = probe(
                runtime, configuration, "seed", "Persistence Proof"
            )
            evidence["data_directory"] = str(prepared.root / "data")

        with installation.running(runtime, base=base, app_version="0.1.0") as (
            configuration,
            prepared,
        ):
            evidence["second_start"] = probe(runtime, configuration, "read")
            evidence["identity_is_stable"] = (
                prepared.identifier == evidence["installation_id"]
            )
            try:
                with installation.running(runtime, base=base, app_version="0.1.0"):
                    evidence["second_process_refused"] = False
            except installation.AlreadyRunning:
                evidence["second_process_refused"] = True

        before = len(list((prepared.root / "backups").glob("*.dump")))
        with installation.running(runtime, base=base, app_version="0.2.0") as (
            configuration,
            prepared,
        ):
            evidence["after_upgrade"] = probe(runtime, configuration, "read")
        evidence["checkpoints_before_upgrade"] = before
        evidence["checkpoints_after_upgrade"] = len(
            list((prepared.root / "backups").glob("*.dump"))
        )

        keepsake = base / "installations" / "unrelated-file"
        keepsake.write_text("must survive")
        installation.erase(base, prepared.identifier)
        evidence["installation_removed"] = not prepared.root.exists()
        evidence["unrelated_file_kept"] = keepsake.exists()
        evidence["base_kept"] = base.is_dir()
        keepsake.unlink()
    finally:
        if temporary is not None:
            temporary.cleanup()
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
