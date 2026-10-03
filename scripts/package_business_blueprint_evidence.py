#!/usr/bin/env python3
"""Package exact approved raw tests with provenance; never generate explanations."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path

# Kept independent of application imports: a build does not need a database.
APPROVED = (
    "test_credit_exposure.py", "test_credit_hold.py", "test_credit_hold_adapters.py",
    "test_fulfillment_readiness.py", "test_proposal_decision_policy.py", "test_down_payments.py",
    "test_stock_blocks.py", "test_movement_corrections.py", "finance/test_available_credits.py",
    "finance/test_settlement_flows.py", "conftest.py",
)


def package(source: Path, output: Path, commit: str = "") -> dict:
    source = source.resolve()
    tests = {}
    for name in APPROVED:
        path = source / name
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError("Evidence path escaped the approved source")
        raw = path.read_bytes()
        destination = output / "tests" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        tests[name] = hashlib.sha256(raw).hexdigest()
    manifest = {"version": 1, "commit": commit, "tests": tests}
    output.mkdir(parents=True, exist_ok=True)
    (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", default="")
    arguments = parser.parse_args()
    package(arguments.source, arguments.output, arguments.commit)
