"""What one order costs, at several company sizes (spec 181 FR-001, FR-006, SC-001).

SC-001 asks for a bounded cost: at most 60 reads and 100 ms of SQL for one order
with its invoice and payment on a company with 100,000 orders, and within 20 % of
the same cost at 1,000. That is a statement about a *curve*, so one measurement
cannot answer it. This records the same order-to-cash at a series of sizes and
reports the ratio between the largest and the smallest.

Run it against a disposable database only:

    REALITY_DATABASE_URL=postgresql+psycopg://…/reality_benchmark_ingest \\
      python -m benchmarks.ingest_cost.runner \\
      --checkpoints 0,250,500 --confirm-disposable --output result.json
"""

from __future__ import annotations

import argparse
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from reality.db.core import Document, Tenant

#: What each measured step is expected to produce, so its cost is reported per
#: record rather than per sweep.
PRODUCES = {
    "order": "sales_order",
    "invoice": "sales_invoice",
    "payment": "customer_payment",
}

from .company import (
    build,
    claim_for,
    execute,
    make_due,
    marked_intake,
    settle_from,
)
from .measure import measured
from .report import IngestResult, write_result


def validate_database_target(database_name: str, *, confirmed: bool) -> None:
    """FR-006: the measurement is refused on a business company.

    The guard is the database name rather than the tenant, because by the time a
    tenant could be inspected the fixture has already written to the database it
    was pointed at.
    """
    if not database_name.startswith("reality_benchmark_"):
        raise ValueError("Database name must begin with reality_benchmark_.")
    if not confirmed:
        raise ValueError("Pass --confirm-disposable to use the benchmark database.")


def _documents(session: Session, tenant_id: str, document_type: str) -> int:
    return int(
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == tenant_id, Document.type == document_type)
        )
        or 0
    )


def _orders(session: Session, tenant_id: str) -> int:
    return _documents(session, tenant_id, "sales_order")


def _grow_to(session, company, target: int) -> None:
    """Record orders until the company has at least `target` of them.

    A single barren sweep is ordinary: the order schedule is not due at every tick,
    and a settlement sweep does its own work instead. Only a run of them means the
    fixture has stopped growing — because the connection throttled itself, or
    because it was paused.
    """
    barren = 0
    while _orders(session, company.tenant_id) < target:
        before = _orders(session, company.tenant_id)
        _run_once(session, company, "demo.generate_orders")
        _run_once(session, company, "demo.settle_orders")
        _run_once(session, company, "demo.settle_orders")
        barren = 0 if _orders(session, company.tenant_id) > before else barren + 1
        if barren >= 12:
            raise RuntimeError(
                f"Twelve sweeps produced no order at {before}. The connection has "
                "stopped or is throttling; the fixture cannot reach the checkpoint."
            )


SETTLEMENT_AHEAD = timedelta(hours=4)


SETTLEMENT_AHEAD = timedelta(hours=4)
#: How many sweeps a measured step may take before giving up on producing a record.
#: A sweep that produced nothing has no cost per record, and reporting its sweep
#: cost as if it had produced one is how the middle of a curve comes out wrong.
ATTEMPTS = 8


def _run_once(session, company, job_type: str) -> bool:
    """One unmeasured occurrence of this job type. True if it ran."""
    make_due(session, company, SETTLEMENT_AHEAD)
    run = claim_for(session, company, job_type)
    if run is None:
        return False
    if job_type == "demo.settle_orders":
        settle_from(session, company, run, SETTLEMENT_AHEAD)
    execute(session, company, run)
    return True


def _measure_step(session, company, engine, job_type: str, label: str):
    """The cost of producing one record of this kind, or None if none was produced.

    Sweeps that produce nothing are ordinary — the schedule is not always due, and
    settlement has nothing to do until an order has aged. They are run and
    discarded rather than averaged in, because the question is what a record
    costs, not what a sweep costs.
    """
    for _ in range(ATTEMPTS):
        make_due(session, company, SETTLEMENT_AHEAD)
        run = claim_for(session, company, job_type)
        if run is None:
            continue
        if job_type == "demo.settle_orders":
            settle_from(session, company, run, SETTLEMENT_AHEAD)
        before = _documents(session, company.tenant_id, PRODUCES[label])
        with measured(engine, label) as cost, marked_intake():
            execute(session, company, run)
        cost.produced = _documents(session, company.tenant_id, PRODUCES[label]) - before
        # Only a sweep that produced exactly one record is kept. A sweep carries a
        # fixed cost — claiming, the throttle, the selection — beside its per-record
        # work, so dividing by two records and by three does not give two readings of
        # the same thing. Comparing such readings across checkpoints once produced a
        # 1.17x "growth" that was nothing but the divisor moving, and it was very
        # nearly published as a finding.
        if cost.produced == 1:
            if cost.interpreting_queries == 0:
                # The wrapper did not reach the handler's call — the same trap the
                # clock fell into. A zero here means the split is not measured, not
                # that interpreting is free, so it is a failure rather than a row.
                raise RuntimeError(
                    "No statement was attributed to interpreting; the intake wrapper "
                    "did not reach the service the handler calls."
                )
            return cost
    return None


def _sample(session, company, engine) -> list[dict]:
    """One order, its invoice and its payment, each measured on its own.

    Settlement is swept twice because the two steps cost differently: the invoice
    reads the order, and the payment walks the customer's history — which is the
    one `research.md` found growing with the company.
    """
    steps = [
        _measure_step(session, company, engine, "demo.generate_orders", "order"),
        _measure_step(session, company, engine, "demo.settle_orders", "invoice"),
        _measure_step(session, company, engine, "demo.settle_orders", "payment"),
    ]
    return [step.as_record() for step in steps if step is not None]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Measure what one order costs as a company grows."
    )
    parser.add_argument(
        "--checkpoints",
        default="0,250,500",
        help="Company sizes in orders at which to measure one order to cash.",
    )
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    database_url = os.environ.get("REALITY_DATABASE_URL", "")
    if not database_url:
        raise ValueError("REALITY_DATABASE_URL is required.")
    validate_database_target(
        make_url(database_url).database or "", confirmed=args.confirm_disposable
    )
    engine = create_engine(database_url)
    if "tenant" not in set(inspect(engine).get_table_names()):
        raise ValueError("Current Reality schema must be applied before the benchmark.")

    checkpoints = sorted({int(value) for value in args.checkpoints.split(",")})
    with Session(engine) as session:
        if session.scalar(select(func.count()).select_from(Tenant)):
            raise ValueError("Benchmark database business tables must be empty.")
        company = build(session)
        # Statistics before the first sample, so the planner is not choosing from
        # an empty table's defaults while the measurement runs.
        session.commit()
        session.execute(text("ANALYZE"))
        session.commit()

        samples = []
        for checkpoint in checkpoints:
            _grow_to(session, company, checkpoint)
            session.execute(text("ANALYZE"))
            session.commit()
            samples.append(
                {
                    "orders_before": _orders(session, company.tenant_id),
                    "steps": _sample(session, company, engine),
                }
            )
        postgresql = str(session.scalar(text("SHOW server_version")))

    result = IngestResult.from_samples(
        samples,
        tenant_id=company.tenant_id,
        git_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        python=sys.version.split()[0],
        platform=platform.platform(),
        postgresql=postgresql,
        created_at=datetime.now(UTC),
    )
    write_result(result, args.output)
    print(result.summary())
    return 0


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
