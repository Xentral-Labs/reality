"""Test helper that pauses an upgrade at a named external-operation boundary."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path


def load_installation():
    script = Path(__file__).with_name("installation.py")
    spec = importlib.util.spec_from_file_location("upgrade_worker_installation", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    runtime = Path(sys.argv[1]).resolve()
    base = Path(sys.argv[2]).resolve()
    phase = sys.argv[3]
    version = sys.argv[4]
    installation = load_installation()
    prepared = installation.resolve(base)
    marker = prepared.root / f"{phase}-ready"

    def pause() -> None:
        marker.write_text("ready\n")
        while True:
            time.sleep(60)

    if phase == "restore":
        original = installation.cluster.restore

        def interrupted_restore(*args, **kwargs):
            pause()
            return original(*args, **kwargs)

        installation.cluster.restore = interrupted_restore
    elif phase == "migration":
        original = installation._migrate

        def interrupted_migration(*args, **kwargs):
            pause()
            return original(*args, **kwargs)

        installation._migrate = interrupted_migration
    else:
        raise ValueError("Unsupported interruption phase.")

    with installation.running(runtime, base=base, app_version=version):
        raise RuntimeError("Upgrade unexpectedly reached product startup.")


if __name__ == "__main__":
    main()
