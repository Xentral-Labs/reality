"""Hold two measurement runs against each other (spec 181 SC-005, User Story 5).

SC-005 asks that two runs on the same commit differ by less than 10 % on every
recorded cost. A measurement nobody has compared with itself cannot be used to
compare two commits either: without knowing its own spread, a difference of five
per cent between yesterday and today means nothing.

Two things are compared differently on purpose. **Counts** — queries, and the
interpreting share of them — are the same arithmetic on any host and are expected
to be identical; a difference of one is reported. **Milliseconds** are not: they
depend on the machine, the page cache and whatever else was running, so they are
held to the tolerance and reported with it. That distinction is the record's own
(`limitations`), and this comparison keeps it rather than averaging it away.

    python -m benchmarks.ingest_cost.compare first.json second.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .report import IngestResult

#: SC-005's threshold. It applies to the timings; the counts are held to exact
#: equality, because a query that ran once yesterday and twice today is a change
#: in the product, not in the weather.
DEFAULT_TOLERANCE = 0.10


class NotComparable(ValueError):
    """The two runs do not measure the same thing, so no difference is meaningful."""


def _load(path: Path) -> IngestResult:
    return IngestResult.model_validate_json(path.read_text(encoding="utf-8"))


def _same_shape(first: IngestResult, second: IngestResult) -> None:
    if first.git_revision != second.git_revision:
        raise NotComparable(
            "SC-005 is about two runs on the same commit: "
            f"{first.git_revision} against {second.git_revision}."
        )
    if len(first.samples) != len(second.samples):
        raise NotComparable(
            f"Different number of checkpoints: {len(first.samples)} "
            f"against {len(second.samples)}."
        )
    for left, right in zip(first.samples, second.samples, strict=True):
        if [step.step for step in left.steps] != [step.step for step in right.steps]:
            raise NotComparable(f"Different steps at {left.orders_before} orders.")


def _relative(first: float, second: float) -> float:
    """How far apart two figures are, as a share of the larger."""
    largest = max(abs(first), abs(second))
    return 0.0 if largest == 0 else abs(first - second) / largest


def compare(
    first: IngestResult, second: IngestResult, tolerance: float = DEFAULT_TOLERANCE
) -> dict[str, Any]:
    """Every recorded cost of the two runs, and where they disagree.

    A finding names the checkpoint, the step and the figure, so a difference is
    attributable to an intake step rather than to "the benchmark" (User Story 5).
    """
    _same_shape(first, second)
    findings: list[dict[str, Any]] = []
    compared = 0
    for left, right in zip(first.samples, second.samples, strict=True):
        if left.orders_before != right.orders_before:
            # The fixture cannot land on a checkpoint exactly: one sweep delivers
            # several orders, so growing "to 250" can stop at 251. That is drift in
            # the company, not in the cost, so it is reported rather than refused.
            findings.append(
                {
                    "orders_before": left.orders_before,
                    "step": "-",
                    "figure": "checkpoint",
                    "kind": "drift",
                    "first": left.orders_before,
                    "second": right.orders_before,
                    "difference": right.orders_before - left.orders_before,
                }
            )
        for step_left, step_right in zip(left.steps, right.steps, strict=True):
            where = {"orders_before": left.orders_before, "step": step_left.step}
            for figure in ("queries", "interpreting_queries", "produced"):
                compared += 1
                values = (getattr(step_left, figure), getattr(step_right, figure))
                if values[0] != values[1]:
                    findings.append(
                        {
                            **where,
                            "figure": figure,
                            "kind": "count",
                            "first": values[0],
                            "second": values[1],
                            "difference": values[1] - values[0],
                        }
                    )
            for figure in ("sql_ms", "interpreting_ms", "wall_ms"):
                compared += 1
                values = (getattr(step_left, figure), getattr(step_right, figure))
                spread = _relative(*values)
                if spread > tolerance:
                    findings.append(
                        {
                            **where,
                            "figure": figure,
                            "kind": "time",
                            "first": round(values[0], 1),
                            "second": round(values[1], 1),
                            "spread": round(spread, 3),
                        }
                    )
    return {
        "git_revision": first.git_revision,
        "tolerance": tolerance,
        "compared": compared,
        "findings": findings,
        "repeatable": not findings,
    }


def render(verdict: dict[str, Any]) -> str:
    headline = (
        f"Two runs on {verdict['git_revision'][:8]}, "
        f"{verdict['compared']} recorded costs, tolerance "
        f"{verdict['tolerance']:.0%} on timings and exact on counts."
    )
    lines = [headline]
    if verdict["repeatable"]:
        lines.append("Every recorded cost agrees: SC-005 is met by this pair.")
        return "\n".join(lines)
    lines.append(f"{len(verdict['findings'])} disagree:")
    for finding in verdict["findings"]:
        where = f"{finding['orders_before']:>6} orders  {finding['step']:<8}"
        if finding["kind"] == "drift":
            lines.append(
                f"  {where} checkpoint: the company held "
                f"{finding['first']} orders against {finding['second']}"
            )
        elif finding["kind"] == "count":
            lines.append(
                f"  {where} {finding['figure']}: "
                f"{finding['first']} → {finding['second']}"
            )
        else:
            lines.append(
                f"  {where} {finding['figure']}: "
                f"{finding['first']} ms → {finding['second']} ms "
                f"({finding['spread']:.0%})"
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare two ingest cost runs (spec 181 SC-005)."
    )
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    verdict = compare(_load(args.first), _load(args.second), args.tolerance)
    print(render(verdict))
    if args.output:
        args.output.write_text(json.dumps(verdict, indent=2) + "\n", encoding="utf-8")
    return 0 if verdict["repeatable"] else 1


if __name__ == "__main__":
    sys.exit(main())
