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
    settle_one,
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
#: How many sweeps a measured step may take before giving up on producing a record.
#: A sweep that produced nothing has no cost per record, and reporting its sweep
#: cost as if it had produced one is how the middle of a curve comes out wrong.
#: Raised from eight when the single-record rule arrived: a settlement sweep is
#: now handed one due item on purpose, but the generator still delivers whatever
#: its profile says, so a sample may need several tries before one sweep carries
#: exactly one record. A try that is rejected is an ordinary unmeasured sweep.
ATTEMPTS = 24


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


#: A settlement sweep costs what its backlog makes it cost. Two runs of this
#: benchmark on the same commit disagreed by 400 queries against 168 for one
#: invoice, and 281 against 208 for one payment, until the backlog was emptied
#: first: the sweep that happened to face one walked it, and the record reported
#: that as the interpretation having become more expensive (spec 181 SC-005,
#: measured 2026-09-20). The bound is here so a settlement that cannot drain
#: fails loudly instead of sweeping for ever.
DRAIN_LIMIT = 200


def _drain_settlement(session, company) -> int:
    """Settle until there is nothing left to settle, and say how long it took.

    The measured steps are about what *one* record costs. A sweep facing five
    orders and a sweep facing none both produce one invoice here — the runner
    keeps only single-record sweeps — but they do not do the same work, so the
    state before the measurement has to be the same every time, not merely
    similar.
    """
    tenant_id = company.tenant_id
    for swept in range(DRAIN_LIMIT):
        before = (
            _documents(session, tenant_id, "sales_invoice"),
            _documents(session, tenant_id, "customer_payment"),
        )
        if not _run_once(session, company, "demo.settle_orders"):
            return swept
        after = (
            _documents(session, tenant_id, "sales_invoice"),
            _documents(session, tenant_id, "customer_payment"),
        )
        if after == before:
            return swept
    raise RuntimeError(
        f"Settlement still had work after {DRAIN_LIMIT} sweeps; "
        "the measurement would report a backlog as the cost of one record."
    )


def _produced_counts(session, tenant_id: str) -> dict[str, int]:
    """How many of each kind the company holds: what a sweep delivered, in full."""
    return {
        document_type: _documents(session, tenant_id, document_type)
        for document_type in set(PRODUCES.values())
    }


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
        if job_type == "demo.settle_orders" and not settle_one(
            session, company, run, SETTLEMENT_AHEAD
        ):
            continue
        before = _produced_counts(session, company.tenant_id)
        with measured(engine, label) as cost, marked_intake():
            execute(session, company, run)
        after = _produced_counts(session, company.tenant_id)
        delivered = {kind: after[kind] - before[kind] for kind in after}
        cost.produced = delivered[PRODUCES[label]]
        # Only a sweep that produced exactly one record is kept. A sweep carries a
        # fixed cost — claiming, the throttle, the selection — beside its per-record
        # work, so dividing by two records and by three does not give two readings of
        # the same thing. Comparing such readings across checkpoints once produced a
        # 1.17x "growth" that was nothing but the divisor moving, and it was very
        # nearly published as a finding.
        # Exactly one record of any kind, not merely one of the kind asked for. A
        # settlement sweep invoices and pays in the same pass: the one that
        # invoiced one order and paid five others produced one `sales_invoice`
        # and cost six records' work, and the record said an invoice had become
        # five times more expensive. Two runs on the same commit disagreed by
        # 519 queries against 168 that way (spec 181 SC-005, 2026-09-20).
        if sum(delivered.values()) == 1 and cost.produced == 1:
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
    # From an empty settlement backlog, so the three steps measure the same thing
    # at every checkpoint and in every run (SC-005).
    _drain_settlement(session, company)
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
