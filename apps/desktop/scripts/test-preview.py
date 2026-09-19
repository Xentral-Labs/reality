"""Run a fresh disposable copy of the disposable macOS development app and remove it on exit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import plistlib
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

DEFAULT_APP = Path(__file__).resolve().parents[1] / "dist/Reality Local Demo Ready No Scroll.app"


@contextmanager
def installation(source: Path):
    if source.is_symlink() or not source.is_dir() or source.suffix != ".app":
        raise ValueError("Expected a real preview .app directory")
    with (source / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    if (
        info.get("CFBundleIdentifier")
        not in {"ai.runreality.local.preview", "ai.runreality.local.development"}
        or info.get("CFBundleExecutable") != "reality-local"
    ):
        raise ValueError(
            "Only the disposable Reality Local development app is supported"
        )
    with tempfile.TemporaryDirectory(
        prefix="reality-preview-test-", dir="/private/tmp"
    ) as root:
        app = Path(root) / "Reality Local.app"
        shutil.copytree(source, app, symlinks=True)
        yield app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path, default=DEFAULT_APP)
    parser.add_argument(
        "--verify", action="store_true", help="Run native checks and quit automatically"
    )
    parser.add_argument(
        "--runs", type=int, default=1, help="Number of consecutive fresh installations"
    )
    args = parser.parse_args()
    if not 1 <= args.runs <= 100:
        parser.error("--runs must be between 1 and 100")
    for number in range(1, args.runs + 1):
        with installation(args.app) as app:
            print(f"Fresh test {number}/{args.runs}: {app}", flush=True)
            onboarding = (app / "Contents/Resources/probe/local-runtime.py").is_file()
            if onboarding:
                print(
                    "Opening company setup with a fresh database; quitting removes its test data.",
                    flush=True,
                )
            else:
                smoke_path = Path(__file__).with_name("runtime-smoke.py")
                spec = importlib.util.spec_from_file_location(
                    "preview_runtime_smoke", smoke_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                print(
                    "Initializing a new disposable PostgreSQL cluster and applying migrations...",
                    flush=True,
                )
                proof = module.smoke(
                    app / "Contents/Resources/runtime", temporary_parent=app.parent
                )
                if list(app.parent.glob("reality-pg-*")):
                    raise RuntimeError("Disposable database cleanup was incomplete")
                print(json.dumps(proof, sort_keys=True), flush=True)
                print(
                    "Fresh database verified, stopped and removed. Opening stateless UI preview.",
                    flush=True,
                )
            command = [str(app / "Contents/MacOS/reality-local")]
            if args.verify:
                command.append("--verify")
            try:
                result = subprocess.run(
                    command, timeout=240 if args.verify else None, check=False
                )
            except subprocess.TimeoutExpired:
                print(
                    "Verification timed out; removing this disposable installation.",
                    flush=True,
                )
                raise SystemExit(2) from None
        print("Disposable app copy removed. Source app preserved.", flush=True)
        if result.returncode:
            raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
