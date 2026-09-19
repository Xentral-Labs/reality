"""Inspect desktop runtime candidates without installing or executing candidate code.

This preflight detects known packaging defects. It is not a signing, dependency
closure, or clean-machine qualification certificate.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath


def dependencies(output: str) -> list[str]:
    return [
        match.group(1)
        for line in output.splitlines()
        if (match := re.match(r"^\s+(.+?) \(compatibility version ", line))
    ]


def external_dependencies(output: str) -> list[str]:
    return [
        path
        for path in dependencies(output)
        if not path.startswith(("@", "/usr/lib/", "/System/Library/"))
    ]


def relative_dependencies(output: str) -> list[str]:
    return [path for path in dependencies(output) if path.startswith("@")]


def library_search_paths(output: str) -> list[str]:
    paths = []
    command = ""
    for line in output.splitlines():
        fields = line.split()
        if fields[:1] == ["cmd"]:
            command = fields[1] if len(fields) == 2 else ""
        if command == "LC_RPATH" and (
            match := re.match(r"\s*path (.+) \(offset \d+\)", line)
        ):
            paths.append(match.group(1))
    return paths


def minimum_macos_versions(output: str) -> list[tuple[int, ...]]:
    versions = []
    command = ""
    for line in output.splitlines():
        fields = line.split()
        if fields[:1] == ["cmd"]:
            command = fields[1] if len(fields) == 2 else ""
        if len(fields) == 2 and (
            (command == "LC_BUILD_VERSION" and fields[0] == "minos")
            or (command == "LC_VERSION_MIN_MACOSX" and fields[0] == "version")
        ):
            versions.append(tuple(int(part) for part in fields[1].split(".")))
    return versions


def minimum_macos_problems(output: str, supported: str) -> list[str]:
    versions = minimum_macos_versions(output)
    if not versions:
        return ["Missing native minimum macOS metadata"]
    ceiling = tuple(int(part) for part in supported.split("."))
    normalized = lambda version: (*version, *(0 for _ in range(3 - len(version))))
    return [
        f"Native minimum macOS {'.'.join(map(str, version))} exceeds {supported}"
        for version in versions
        if normalized(version) > normalized(ceiling)
    ]


def tree_problems(root: Path) -> list[str]:
    root = root.resolve(strict=True)
    problems = []
    for path in sorted(root.rglob("*")):
        if not path.is_symlink():
            continue
        relative = path.relative_to(root)
        try:
            resolved = path.resolve(strict=True)
        except (OSError, RuntimeError):
            problems.append(f"{relative}: broken or cyclic symlink")
            continue
        if not resolved.is_relative_to(root):
            problems.append(f"{relative}: symlink escapes runtime")
        elif Path(os.readlink(path)).is_absolute():
            problems.append(f"{relative}: absolute symlink is not relocatable")
    return problems


def wheel_problems(wheel: Path) -> list[str]:
    problems = []
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        for name in names:
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name:
                problems.append(f"unsafe archive entry: {name}")
        for required in (
            "reality/config/command_catalog.yaml",
            "reality/config/data_model.yaml",
            "reality/migrations/env.py",
        ):
            if required not in names:
                problems.append(f"missing resource: {required}")
        for required in (
            "reality/migrations/versions/",
            "reality/storylines/",
            "reality/examples/imports/",
        ):
            if not any(
                name.startswith(required) and not name.endswith("/") for name in names
            ):
                problems.append(f"missing resource group: {required}")
        if (corrupt := archive.testzip()) is not None:
            problems.append(f"corrupt archive entry: {corrupt}")
    return problems


def inspect_binary(path: Path) -> dict:
    env = dict(os.environ)
    clt = Path("/Library/Developer/CommandLineTools")
    if clt.is_dir():
        env["DEVELOPER_DIR"] = str(clt)
    result = subprocess.run(
        check=False,
        args=["/usr/bin/otool", "-L", str(path)],
        capture_output=True,
        text=True,
        timeout=15,
        env=env,
    )
    if result.returncode:
        return {"path": str(path), "error": result.stderr.strip() or "otool failed"}
    return {
        "path": str(path),
        "external_dependencies": external_dependencies(result.stdout),
        "relative_dependencies_requiring_validation": relative_dependencies(
            result.stdout
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", type=Path)
    parser.add_argument("--tree", type=Path)
    parser.add_argument("--binary", type=Path, action="append", default=[])
    args = parser.parse_args()
    if not (args.wheel or args.tree or args.binary):
        parser.error("choose --wheel, --tree or --binary")
    report = {
        "qualification": "preflight only; clean-Mac execution still required",
        "problems": [],
    }
    try:
        if args.wheel:
            report["problems"].extend(wheel_problems(args.wheel))
        if args.tree:
            report["problems"].extend(tree_problems(args.tree))
        if args.binary:
            if platform.system() != "Darwin":
                raise ValueError("Mach-O inspection requires macOS")
            report["binaries"] = [inspect_binary(path) for path in args.binary]
            for binary in report["binaries"]:
                if "error" in binary:
                    report["problems"].append(binary["error"])
                report["problems"].extend(binary.get("external_dependencies", []))
    except (
        OSError,
        ValueError,
        zipfile.BadZipFile,
        subprocess.TimeoutExpired,
    ) as error:
        report["problems"].append(str(error))
    print(json.dumps(report, indent=2))
    return 1 if report["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
