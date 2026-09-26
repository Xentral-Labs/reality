"""Create one durable recovery boundary and terminate without cleanup."""

from __future__ import annotations

import importlib.util
import os
import signal
import sys
from pathlib import Path


def load_recovery():
    script = Path(__file__).resolve().parents[2] / "scripts/recovery.py"
    spec = importlib.util.spec_from_file_location("crash_worker_recovery", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def crash() -> None:
    os.kill(os.getpid(), signal.SIGKILL)


def main() -> None:
    root = Path(sys.argv[1])
    boundary = sys.argv[2]
    recovery = load_recovery()
    active = recovery.resolve_active(root)
    staged = recovery.begin_stage(
        root, source=active.name, from_version="0.1.0", to_version="0.2.0"
    )
    (staged / "partial-restore").write_bytes(b"not authoritative")
    if boundary == "preparing":
        crash()
    if boundary in recovery.UPGRADE_PHASES:
        recovery.record_phase(root, staged.name, boundary)
        crash()
    recovery.mark_validated(root, staged.name, schema_revision="0099_example")
    if boundary == "validated":
        crash()

    atomic_pointer = recovery._atomic_pointer

    def interrupted_pointer(target, identifier):
        if boundary == "after-pointer":
            atomic_pointer(target, identifier)
        crash()

    recovery._atomic_pointer = interrupted_pointer
    recovery.activate(root, staged.name)
    raise RuntimeError("Crash boundary was not reached.")


if __name__ == "__main__":
    main()
