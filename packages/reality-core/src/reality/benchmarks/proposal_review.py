"""Measure warmed Proposal Review service latency without HTTP or browser overhead."""

from __future__ import annotations

import argparse
import math
import time
from collections.abc import Callable, Sequence
from typing import Any

from reality.db.core import Session
from reality.services.proposal_reviews import proposal_review


def percentile(values: Sequence[float], proportion: float) -> float:
    """Return the nearest-rank percentile for a non-empty sequence."""
    if not values:
        raise ValueError("At least one duration is required.")
    if not 0 < proportion <= 1:
        raise ValueError(
            "The percentile proportion must be greater than 0 and at most 1."
        )
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * proportion) - 1]


def measure(
    read: Callable[[], Any], runs: int, clock: Callable[[], float] = time.perf_counter
) -> list[float]:
    """Warm once, then return service-only durations in milliseconds."""
    if runs < 1:
        raise ValueError("Runs must be at least 1.")
    read()
    durations = []
    for _ in range(runs):
        started = clock()
        read()
        durations.append((clock() - started) * 1000)
    return durations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--proposal", required=True)
    parser.add_argument("--runs", type=int, default=20)
    parser.add_argument("--max-p95-ms", type=float, default=200)
    arguments = parser.parse_args()

    with Session() as session:
        durations = measure(
            lambda: proposal_review(session, arguments.tenant, arguments.proposal),
            arguments.runs,
        )
    p95 = percentile(durations, 0.95)
    rendered = ",".join(f"{duration:.2f}" for duration in durations)
    print(f"runs={len(durations)} durations_ms={rendered} p95_ms={p95:.2f}")
    if p95 > arguments.max_p95_ms:
        raise SystemExit(
            f"Proposal Review p95 {p95:.2f} ms exceeds {arguments.max_p95_ms:.2f} ms."
        )


if __name__ == "__main__":
    main()
