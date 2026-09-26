"""Write deterministic SHA-256 manifests for macOS release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def entries(root: Path) -> list[dict]:
    root = root.resolve(strict=True)
    result = []
    paths = [root] if root.is_file() else sorted(root.rglob("*"))
    for path in paths:
        relative = path.name if root.is_file() else path.relative_to(root).as_posix()
        if path.is_symlink():
            result.append(
                {"path": relative, "type": "symlink", "target": os.readlink(path)}
            )
        elif path.is_file():
            result.append(
                {
                    "path": relative,
                    "type": "file",
                    "bytes": path.stat().st_size,
                    "sha256": digest(path),
                }
            )
    return result


def manifest(root: Path, *, version: str, artifact: str) -> dict:
    return {
        "format_version": 1,
        "product_version": version,
        "artifact": artifact,
        "entries": entries(root),
    }


def differences(expected: dict, actual: dict) -> list[str]:
    """Describe deterministic release-manifest differences without hiding paths."""
    problems = []
    for field in ("format_version", "product_version", "artifact"):
        if expected.get(field) != actual.get(field):
            problems.append(field)
    expected_entries = {entry["path"]: entry for entry in expected.get("entries", [])}
    actual_entries = {entry["path"]: entry for entry in actual.get("entries", [])}
    for path in sorted(expected_entries.keys() | actual_entries.keys()):
        if expected_entries.get(path) != actual_entries.get(path):
            problems.append(path)
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--compare-to", type=Path)
    arguments = parser.parse_args()
    value = manifest(
        arguments.root, version=arguments.version, artifact=arguments.artifact
    )
    if arguments.compare_to:
        expected = json.loads(arguments.compare_to.read_text())
        if problems := differences(expected, value):
            raise SystemExit("Release manifest differs: " + ", ".join(problems[:20]))
    arguments.output.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
