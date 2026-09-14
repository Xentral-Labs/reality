"""Fail-safe changed-path classification for the backend quality gate."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

BACKEND_PREFIXES = (
    "packages/reality-core/",
    "apps/api/",
    "apps/mcp/",
    "apps/scheduler/",
    "apps/worker/",
    "helm/",
    "infra/",
)
BACKEND_FILES = {
    ".github/workflows/quality.yml",
    "Dockerfile",
    "Makefile",
    "compose.yml",
    "compose.dev.yml",
    "compose.analytics.yml",
    "scripts/ci_backend_changes.py",
    "scripts/ci_backend_test_shard.py",
    "scripts/test_ci_backend_changes.py",
    "scripts/test_ci_backend_test_shard.py",
    "scripts/test_quality_workflow.py",
}


def requires_backend(paths: Iterable[str]) -> bool:
    """Return true for backend changes and for missing or malformed input."""
    candidates = list(paths)
    if not candidates:
        return True
    for path in candidates:
        if not path or path.startswith("/") or "\0" in path:
            return True
        if path in BACKEND_FILES or path.startswith(BACKEND_PREFIXES):
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--null", action="store_true", help="read NUL-delimited paths")
    args = parser.parse_args()
    separator = "\0" if args.null else "\n"
    raw = sys.stdin.read()
    paths = raw.split(separator)
    if raw.endswith(separator):
        paths.pop()
    print(f"changed={'true' if requires_backend(paths) else 'false'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
