"""Start the installed product; the persistent installation keeps its data until erased.

Setting REALITY_DESKTOP_DISPOSABLE=1 selects the fresh-test harness from spec 239
instead, which initializes a new cluster and removes it again on exit.
"""

import importlib.util
import json
import os
import plistlib
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import uuid4

SCRIPTS = Path(__file__).resolve().parent
RUNTIME = SCRIPTS.parent / "runtime"
BUNDLE = SCRIPTS.parents[2] / "Info.plist"


def serve(configuration, root):
    python = RUNTIME / "python/bin/python3.12"
    config = {
        "database_url": configuration["REALITY_DATABASE_URL"],
        "core_root": str(RUNTIME / "core"),
        "artifact_root": str(root / "artifacts"),
        "frontend": str(SCRIPTS.parent / "frontend"),
        "installation_id": configuration.get("REALITY_INSTALLATION_ID") or str(uuid4()),
    }
    env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
    # Separate exclusive preparation process; API startup never performs migrations.
    prepared = subprocess.run(
        [str(python), "-I", str(SCRIPTS / "local-product.py"), "--prepare"],
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
            [str(python), "-I", str(SCRIPTS / "local-background.py"), role],
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
        [str(python), "-I", str(SCRIPTS / "local-product.py")],
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


def main():
    if disposable():
        load("runtime-smoke").smoke(RUNTIME, operation=serve)
        return
    installation = load("installation")
    identifier, version = bundle()
    base = installation.base_directory(identifier or installation.DEFAULT_IDENTIFIER)
    try:
        with installation.running(RUNTIME, base=base, app_version=version) as (
            configuration,
            prepared,
        ):
            serve(configuration, prepared.root)
    except installation.AlreadyRunning as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
