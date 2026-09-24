"""Build deterministic backend test-file shards, balanced by measured duration.

File size is a poor predictor of test time: one file that seeds a demo company
costs more than a hundred unit-test files. The shards are therefore weighted by
recorded seconds from `scripts/backend_test_durations.json`, refreshed with
`scripts/record_backend_test_durations.py` from a JUnit report.
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

DURATIONS = Path(__file__).with_name("backend_test_durations.json")


def load_durations(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    recorded = json.loads(path.read_text())
    return {key: float(value) for key, value in recorded.get("files", {}).items()}


def weigh(files: list[Path], root: Path, durations: dict[str, float]) -> dict[Path, float]:
    """Seconds where they are known, the median of the known ones where they are not."""
    known = [durations[str(path.relative_to(root))] for path in files if str(path.relative_to(root)) in durations]
    fallback = statistics.median(known) if known else 1.0
    return {
        path: durations.get(str(path.relative_to(root)), fallback) for path in files
    }


def shard_files(root: Path, total: int, durations: dict[str, float] | None = None) -> list[list[Path]]:
    if total < 1:
        raise ValueError("total must be positive")
    files = sorted(root.rglob("test_*.py"))
    if not files:
        raise ValueError(f"no test files found below {root}")
    weights_by_file = weigh(files, root, durations if durations is not None else load_durations(DURATIONS))
    # Longest first, each file to the lightest shard: the classic greedy balance.
    files.sort(key=lambda path: (-weights_by_file[path], str(path)))
    shards: list[list[Path]] = [[] for _ in range(total)]
    loads = [0.0] * total
    for path in files:
        target = min(range(total), key=lambda index: (loads[index], index))
        shards[target].append(path)
        loads[target] += weights_by_file[path]
    return shards


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--total", type=int, required=True)
    parser.add_argument("--relative-to", type=Path, default=Path.cwd())
    parser.add_argument("--durations", type=Path, default=DURATIONS)
    parser.add_argument(
        "--report",
        action="store_true",
        help="print each shard's file count and predicted seconds instead of one shard",
    )
    args = parser.parse_args()
    if not 0 <= args.shard < args.total:
        parser.error("shard must be between zero and total minus one")
    recorded = load_durations(args.durations)
    shards = shard_files(args.root, args.total, recorded)
    if args.report:
        weights = weigh(sorted(args.root.rglob("test_*.py")), args.root, recorded)
        for index, shard in enumerate(shards):
            seconds = sum(weights[path] for path in shard)
            print(f"shard {index}: {len(shard)} files, {seconds:.0f}s predicted")
        return 0
    for path in shards[args.shard]:
        print(path.relative_to(args.relative_to))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
