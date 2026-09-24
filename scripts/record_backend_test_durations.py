"""Write the per-file backend test durations the CI shard split balances on.

The numbers come from CI, not from a developer machine: each shard uploads its
JUnit report, and the reports are merged here.

    python3 scripts/record_backend_test_durations.py shard-0.xml shard-1.xml

A set of reports that does not cover every test file is refused, so a partial run
cannot quietly unbalance the shards.
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ElementTree
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

TESTS = Path("packages/reality-core/tests")
TARGET = Path(__file__).with_name("backend_test_durations.json")


def test_file(classname: str, tests: Path) -> str | None:
    """Map a JUnit classname to its file.

    pytest's default report carries no file attribute, and a class-based test puts
    the class into the same dotted name, so the longest prefix that exists on disk
    is the file.
    """
    parts = classname.split(".")
    while parts:
        candidate = tests.parent.joinpath(*parts).with_suffix(".py")
        if candidate.exists():
            return str(candidate.relative_to(tests))
        parts.pop()
    return None


def durations(reports: list[Path], tests: Path) -> dict[str, float]:
    seconds: dict[str, float] = defaultdict(float)
    for report in reports:
        for case in ElementTree.parse(report).getroot().iter("testcase"):
            path = case.get("file") or test_file(case.get("classname", ""), tests)
            if path:
                seconds[path] += float(case.get("time", 0.0))
    return dict(seconds)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", type=Path, nargs="+")
    parser.add_argument("--target", type=Path, default=TARGET)
    parser.add_argument("--tests", type=Path, default=TESTS)
    args = parser.parse_args()
    measured = durations(args.reports, args.tests)
    if not measured:
        print("no test cases in the reports", file=sys.stderr)
        return 1
    present = {str(path.relative_to(args.tests)) for path in args.tests.rglob("test_*.py")}
    missing = present - set(measured)
    if missing:
        print(
            f"{len(missing)} test files are absent from the reports,"
            f" e.g. {sorted(missing)[:3]}",
            file=sys.stderr,
        )
        return 1
    args.target.write_text(
        json.dumps(
            {
                "recorded_at": datetime.now(UTC).date().isoformat(),
                "unit": "seconds",
                "files": {key: round(value, 2) for key, value in sorted(measured.items())},
            },
            indent=2,
        )
        + "\n"
    )
    print(f"recorded {len(measured)} files in {args.target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
