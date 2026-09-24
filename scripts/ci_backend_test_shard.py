"""Build deterministic backend test-file shards.

The shards are balanced by file count, which measured better than anything
cleverer. Weighing the recorded seconds instead balanced the shards perfectly on
paper — 1401s against 1401s — and made CI 20% slower twice over, because a
shard's real time is not the sum of its files' times: the demo-seeding tests
queue on the one PostgreSQL service, so co-locating them inflates exactly the
number the model trusted. `--dist worksteal` already balances inside a shard;
what matters here is only that the database-heavy files stay spread across both.

    critical path, two samples each
    by file count                    742s, 788s
    by recorded seconds, heavy first 921s, 920s
    by recorded seconds, path order  888s

`scripts/backend_test_durations.json` stays as the record of where the time
goes — it is how the twenty-second demo seed per test was found — and
`--report` prints it. It does not decide the split.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DURATIONS = Path(__file__).with_name("backend_test_durations.json")


def load_durations(path: Path) -> dict[str, float]:
    if not path.exists():
        return {}
    recorded = json.loads(path.read_text())
    return {key: float(value) for key, value in recorded.get("files", {}).items()}


def shard_files(root: Path, total: int) -> list[list[Path]]:
    if total < 1:
        raise ValueError("total must be positive")
    files = sorted(root.rglob("test_*.py"))
    if not files:
        raise ValueError(f"no test files found below {root}")
    # Round robin over the path order: every shard gets the same count, and files
    # that sit together in the tree — which tend to share a cost profile — land in
    # different shards.
    shards: list[list[Path]] = [[] for _ in range(total)]
    for index, path in enumerate(files):
        shards[index % total].append(path)
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
        help="print each shard's file count and its recorded seconds, if any",
    )
    args = parser.parse_args()
    if not 0 <= args.shard < args.total:
        parser.error("shard must be between zero and total minus one")
    shards = shard_files(args.root, args.total)
    if args.report:
        recorded = load_durations(args.durations)
        for index, shard in enumerate(shards):
            seconds = sum(
                recorded.get(str(path.relative_to(args.root)), 0.0) for path in shard
            )
            print(f"shard {index}: {len(shard)} files, {seconds:.0f}s recorded")
        return 0
    for path in shards[args.shard]:
        print(path.relative_to(args.relative_to))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
