"""Build deterministic, size-balanced backend test-file shards."""

from __future__ import annotations

import argparse
from pathlib import Path


def shard_files(root: Path, total: int) -> list[list[Path]]:
    if total < 1:
        raise ValueError("total must be positive")
    files = sorted(
        root.rglob("test_*.py"), key=lambda path: (-path.stat().st_size, str(path))
    )
    if not files:
        raise ValueError(f"no test files found below {root}")
    shards: list[list[Path]] = [[] for _ in range(total)]
    weights = [0] * total
    for path in files:
        target = min(range(total), key=lambda index: (weights[index], index))
        shards[target].append(path)
        weights[target] += path.stat().st_size
    return shards


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--shard", type=int, required=True)
    parser.add_argument("--total", type=int, required=True)
    parser.add_argument("--relative-to", type=Path, default=Path.cwd())
    args = parser.parse_args()
    if not 0 <= args.shard < args.total:
        parser.error("shard must be between zero and total minus one")
    for path in shard_files(args.root, args.total)[args.shard]:
        print(path.relative_to(args.relative_to))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
