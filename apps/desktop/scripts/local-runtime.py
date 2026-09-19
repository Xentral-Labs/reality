"""Disposable onboarding development runtime; no persistent installation is touched."""

import importlib.util
import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from uuid import uuid4

SCRIPTS = Path(__file__).resolve().parent
RUNTIME = SCRIPTS.parent / "runtime"


def serve(configuration, root):
    python = RUNTIME / "python/bin/python3.12"
    config = {
        "database_url": configuration["REALITY_DATABASE_URL"],
        "core_root": str(RUNTIME / "core"),
        "artifact_root": str(root / "artifacts"),
        "frontend": str(SCRIPTS.parent / "frontend"),
        "installation_id": str(uuid4()),
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
            if not stopping.is_set() and any(child.poll() is not None for child in roles):
                raise RuntimeError("Local background process failed.")
            time.sleep(0.2)
        code = process.returncode
        if code:
            raise RuntimeError("Local product process failed.")
        return {"stopped": True}
    finally:
        stop_all()


def main():
    spec = importlib.util.spec_from_file_location(
        "runtime_smoke", SCRIPTS / "runtime-smoke.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.smoke(RUNTIME, operation=serve)


if __name__ == "__main__":
    main()
