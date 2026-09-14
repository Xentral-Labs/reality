#!/usr/bin/env python3
"""Report the next free Spec Kit feature number across local and remote work.

`.specify/scripts/bash/create-new-feature.sh` derives the next number from the
`specs/` directory of the current checkout only. Two branches created from the same
base therefore pick the same number without noticing, which is how
`specs/022-auditable-document-line-corrections` and `specs/022-public-site` both
became 022.

That script is vendored: it is listed with its SHA-256 digest in
`.specify/integrations/speckit.manifest.json`, so editing it in place would be lost on
the next Spec Kit upgrade. This helper stays outside the vendored tree instead and
widens the search to the default branch and every remote branch name. Pass its result
to Spec Kit explicitly:

    specify ... --number "$(python3 scripts/next_feature_number.py)"

A collision that still reaches a pull request fails `scripts/check_spec_policy.py`.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUMBER_PREFIX = re.compile(r"^(\d{3})-[a-z0-9-]+$")
DEFAULT_REF = "origin/main"
MAX_FEATURE_NUMBER = 999


def git_output(*args: str) -> list[str]:
    """Return trimmed git output, or nothing when the command is unavailable."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return []
    if result.returncode:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _numbers(names: list[str]) -> set[int]:
    found: set[int] = set()
    for name in names:
        match = NUMBER_PREFIX.match(name)
        if match:
            found.add(int(match.group(1)))
    return found


def local_specs() -> set[int]:
    specs = ROOT / "specs"
    if not specs.is_dir():
        return set()
    return _numbers([entry.name for entry in specs.iterdir() if entry.is_dir()])


def default_branch_specs(ref: str) -> set[int]:
    """Numbers already merged into the default branch."""
    if not git_output("rev-parse", "--verify", "--quiet", ref):
        return set()
    listed = git_output("ls-tree", "-d", "--name-only", f"{ref}:specs")
    return _numbers([Path(name).name for name in listed])


def remote_branch_names() -> set[int]:
    """Numbers claimed by pushed branches, including work not yet merged."""
    refs = git_output("for-each-ref", "--format=%(refname:strip=3)", "refs/remotes")
    return _numbers(refs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ref",
        default=DEFAULT_REF,
        help=f"Default-branch ref to inspect (default: {DEFAULT_REF})",
    )
    parser.add_argument(
        "--explain",
        action="store_true",
        help="Also report where each claimed number was found",
    )
    args = parser.parse_args()

    sources = {
        "local specs/": local_specs(),
        f"{args.ref} specs/": default_branch_specs(args.ref),
        "remote branch names": remote_branch_names(),
    }
    claimed = set().union(*sources.values()) if sources else set()
    following = max(claimed) + 1 if claimed else 1
    if following > MAX_FEATURE_NUMBER:
        print(
            f"No free feature number below {MAX_FEATURE_NUMBER + 1}", file=sys.stderr
        )
        return 1

    if args.explain:
        for label, numbers in sources.items():
            listed = ", ".join(f"{number:03d}" for number in sorted(numbers)) or "none"
            print(f"{label}: {listed}", file=sys.stderr)
        print(f"highest claimed: {max(claimed):03d}", file=sys.stderr)

    print(f"{following:03d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
