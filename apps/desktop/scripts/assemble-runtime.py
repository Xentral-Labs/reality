"""Assemble the existing core into a new runtime using an offline hashed wheelhouse."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path

from runtime_audit import tree_problems, wheel_problems

SCRIPTS = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "runtime_builder", SCRIPTS / "build-runtime.py"
)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def assemble(runtime: Path, wheelhouse: Path, core_wheel: Path, output: Path) -> None:
    builder.require_new_output(output)
    if output.resolve().is_relative_to(runtime.resolve()):
        raise ValueError("Assembly output must be outside the source runtime")
    builder.validate_runtime_layout(runtime)
    if problems := wheel_problems(core_wheel):
        raise ValueError("\n".join(problems))
    if problems := tree_problems(runtime):
        raise ValueError("\n".join(problems))
    manifest = json.loads((runtime / "runtime-manifest.json").read_text())
    env = builder.build_environment(manifest["dependencies"]["minimum_macos"])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix="desktop-assemble-", dir=output.parent
    ) as temporary:
        staged = Path(temporary) / "runtime"
        shutil.copytree(runtime, staged, symlinks=True)
        python = staged / "python/bin/python3.12"
        requirements = SCRIPTS / "python-requirements.lock"
        print("Installing locked dependencies from the offline wheelhouse", flush=True)
        builder.run(
            [
                str(python),
                "-I",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-index",
                "--no-compile",
                "--only-binary=:all:",
                "--require-hashes",
                "--find-links",
                str(wheelhouse),
                "-r",
                str(requirements),
            ],
            env,
        )
        builder.run(
            [
                str(python),
                "-I",
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--no-index",
                "--no-deps",
                "--no-compile",
                str(core_wheel),
            ],
            env,
        )
        builder.run([str(python), "-I", "-m", "pip", "check"], env)
        core = staged / "core"
        core.mkdir()
        shutil.copy2(
            SCRIPTS.parents[2] / "packages/reality-core/alembic.ini",
            core / "alembic.ini",
        )
        installed = staged / "python/lib/python3.12/site-packages/reality"
        for name in ("migrations", "config", "storylines"):
            shutil.copytree(installed / name, core / name)
        shutil.copytree(installed / "examples/imports", core / "fixtures/imports")
        shutil.copy2(requirements, staged / "python-requirements.lock")
        print("Auditing and signing bundled native extensions", flush=True)
        manifest["native_binaries"] = builder.relocate_libraries(staged, env)
        if problems := tree_problems(staged):
            raise ValueError("\n".join(problems))
        manifest["core_wheel"] = {
            "name": core_wheel.name,
            "sha256": hashlib.sha256(core_wheel.read_bytes()).hexdigest(),
        }
        manifest["requirements_sha256"] = hashlib.sha256(
            requirements.read_bytes()
        ).hexdigest()
        manifest["qualification"] = "assembled-spike; database smoke pending"
        (staged / "runtime-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        builder.require_new_output(output)
        staged.rename(output)
    print(
        json.dumps(
            {"output": str(output), "native_binaries": manifest["native_binaries"]},
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("runtime", "wheelhouse", "core-wheel", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    args = parser.parse_args()
    try:
        assemble(
            args.runtime.resolve(),
            args.wheelhouse.resolve(),
            args.core_wheel.resolve(),
            args.output.absolute(),
        )
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, f"Runtime assembly failed: {error}\n")


if __name__ == "__main__":
    main()
