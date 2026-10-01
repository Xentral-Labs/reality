"""Peak intake: 10,000 shop orders in two hours (spec 300 FR-003, journey L07).

What a Black Friday asks of Reality, measured on the path a shop order takes:
1. each order arrives as a Shopify payload and is stored with its import job;
2. the jobs are worked by `process_pending_import_jobs`, the service the Web
   (`POST /import-jobs/work`) and the CLI call, from one or more processes;
3. every promise is then reserved from four parallel connections.

The run then checks:
- every order was interpreted exactly once;
- no item is reserved beyond its stock;
- the `item_oversold` finding states exactly the demand that stock cannot cover.

The time target is recorded, never enforced: a run that misses it is a
measurement, not a failure. Run it against a disposable database only:

    REALITY_DATABASE_URL=postgresql+psycopg://…/reality_benchmark_peak \\
      python -m benchmarks.peak_intake.runner \\
      --orders 10000 --processes 4 --confirm-disposable --output result.json
"""

from __future__ import annotations

import argparse
import json
import multiprocessing
import os
import platform
import subprocess
import sys
import time
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

#: Journey L07: 10,000 orders within two hours.
TARGET_SECONDS = 2 * 60 * 60
TARGET_ORDERS = 10_000


def validate_database_target(database_name: str, *, confirmed: bool) -> None:
    """The run is refused on any database that is not a named disposable one."""
    if not database_name.startswith("reality_benchmark_"):
        raise ValueError("Database name must begin with reality_benchmark_.")
    if not confirmed:
        raise ValueError("Pass --confirm-disposable to use the benchmark database.")


def _engine(url: str):
    return create_engine(url, pool_pre_ping=True)


def _work_jobs(url: str, tenant_id: str, queue) -> None:
    """One worker process: work pending import jobs until none are left."""
    from reality.services import core

    engine = _engine(url)
    calls = completed = failed = 0
    started = time.perf_counter()
    with Session(engine, expire_on_commit=False) as session:
        while True:
            done, refused = core.process_pending_import_jobs(
                session, tenant_id, limit=100
            )
            session.commit()
            calls += 1
            completed += done
            failed += refused
            if done + refused == 0:
                break
    elapsed = time.perf_counter() - started
    engine.dispose()
    queue.put(
        {"calls": calls, "completed": completed, "failed": failed, "seconds": elapsed}
    )


def _reserve(url: str, tenant_id: str, commitment_ids: list[str], queue) -> None:
    """One connection reserving its share of the promises."""
    from reality.services import core

    engine = _engine(url)
    reserved = refused = 0
    started = time.perf_counter()
    with Session(engine, expire_on_commit=False) as session:
        for commitment_id in commitment_ids:
            try:
                core.reserve(session, tenant_id, commitment_id)
                reserved += 1
            except core.InvalidOperation:
                session.rollback()
                refused += 1
    elapsed = time.perf_counter() - started
    engine.dispose()
    queue.put({"reserved": reserved, "refused": refused, "seconds": elapsed})


def _parallel(target, arguments: list[tuple]) -> tuple[float, list[dict]]:
    context = multiprocessing.get_context("spawn")
    queue = context.Queue()
    workers = [
        context.Process(target=target, args=(*args, queue)) for args in arguments
    ]
    started = time.perf_counter()
    for worker in workers:
        worker.start()
    results = [queue.get() for _ in workers]
    for worker in workers:
        worker.join()
    elapsed = time.perf_counter() - started
    if any(worker.exitcode for worker in workers):
        raise RuntimeError("A benchmark process failed.")
    return elapsed, results


def _checks(session: Session, tenant_id: str) -> dict[str, Any]:
    from reality.db.core import (
        Commitment,
        Document,
        ImportJob,
        Location,
        Reservation,
        SourceRecord,
    )
    from reality.services import core
    from reality.services.exceptions import _item_oversold_exceptions

    per_source = session.execute(
        select(SourceRecord.external_id, func.count(Document.id))
        .join(
            Document,
            (Document.tenant_id == SourceRecord.tenant_id)
            & (Document.source_record_id == SourceRecord.id),
        )
        .where(
            SourceRecord.tenant_id == tenant_id,
            SourceRecord.source_system == "shopify",
            Document.type == "sales_order",
        )
        .group_by(SourceRecord.external_id)
    ).all()
    over_reserved = []
    locations = list(
        session.scalars(select(Location.id).where(Location.tenant_id == tenant_id))
    )
    reserved_items = set(
        session.scalars(
            select(Reservation.item_id).where(
                Reservation.tenant_id == tenant_id, Reservation.status == "active"
            )
        )
    )
    for item_id in sorted(reserved_items):
        for location_id in locations:
            reserved = core.active_reserved(session, tenant_id, item_id, location_id)
            stock = core.stock_at(session, tenant_id, item_id, location_id)
            if reserved > stock:
                over_reserved.append(
                    {"item_id": item_id, "reserved": str(reserved), "stock": str(stock)}
                )
    demand: dict[str, Decimal] = defaultdict(Decimal)
    short_promises = 0
    for commitment in session.scalars(
        select(Commitment).where(
            Commitment.tenant_id == tenant_id,
            Commitment.type == "customer_delivery",
            Commitment.status == "open",
        )
    ):
        open_quantity = core.open_quantity(session, tenant_id, commitment.id)
        demand[commitment.item_id] += open_quantity
        held = session.scalar(
            select(func.coalesce(func.sum(Reservation.quantity), 0)).where(
                Reservation.tenant_id == tenant_id,
                Reservation.commitment_id == commitment.id,
                Reservation.status == "active",
            )
        )
        if Decimal(held) < open_quantity:
            short_promises += 1
    expected = {
        item_id: quantity - core.stock_at(session, tenant_id, item_id)
        for item_id, quantity in demand.items()
        if quantity > core.stock_at(session, tenant_id, item_id)
    }
    found = {
        row.record_id: row.causal_values["shortfall_quantity"]
        for row in _item_oversold_exceptions(session, tenant_id, core.now())
    }
    jobs = dict(
        session.execute(
            select(ImportJob.status, func.count())
            .where(ImportJob.tenant_id == tenant_id)
            .group_by(ImportJob.status)
        ).all()
    )
    return {
        "sales_orders": sum(count for _, count in per_source),
        "orders_interpreted_more_than_once": sum(
            1 for _, count in per_source if count > 1
        ),
        "import_jobs": {status: int(count) for status, count in jobs.items()},
        "over_reserved_items": over_reserved,
        "promises_not_fully_reserved": short_promises,
        "oversold_items": len(found),
        "oversold_matches_demand_less_stock": found == expected,
    }


def run(
    url: str, *, orders: int, processes: int, items: int = 200, seed: int = 300
) -> dict[str, Any]:
    """One measured peak: store, work, reserve and check."""
    from reality.db.core import Commitment, Tenant
    from reality.services import core

    from .company import build, payloads

    os.environ["REALITY_DATABASE_URL"] = url
    engine = _engine(url)
    with Session(engine, expire_on_commit=False) as session:
        if session.scalar(select(func.count()).select_from(Tenant)):
            raise ValueError("Benchmark database business tables must be empty.")
        company = build(session, orders=orders, items=items, seed=seed)
        started = time.perf_counter()
        for payload in payloads(company, orders=orders, seed=seed):
            core.enqueue_shopify_order(
                session,
                company.tenant_id,
                payload,
                company.company_party_id,
                company.customer_party_id,
                company.location_id,
            )
        session.commit()
        stored = time.perf_counter() - started
        session.execute(text("ANALYZE"))
        session.commit()

    worked_wall, workers = _parallel(_work_jobs, [(url, company.tenant_id)] * processes)

    with Session(engine, expire_on_commit=False) as session:
        promises = list(
            session.scalars(
                select(Commitment.id)
                .where(
                    Commitment.tenant_id == company.tenant_id,
                    Commitment.type == "customer_delivery",
                    Commitment.status == "open",
                )
                .order_by(Commitment.created_at, Commitment.id)
            )
        )
    connections = 4
    reserving_wall, reservers = _parallel(
        _reserve,
        [
            (url, company.tenant_id, promises[index::connections])
            for index in range(connections)
        ],
    )

    with Session(engine, expire_on_commit=False) as session:
        checks = _checks(session, company.tenant_id)
        postgresql = str(session.scalar(text("SHOW server_version")))
    engine.dispose()

    failed = checks["import_jobs"].get("failed", 0)
    # The slowest process from its own first query to its last: process start-up
    # and imports are not intake. The wall time including them is kept beside it.
    worked = max(row["seconds"] for row in workers)
    reserving = max(row["seconds"] for row in reservers)
    return {
        "orders": orders,
        "items": items,
        "seed": seed,
        "store": {"seconds": round(stored, 2)},
        "intake": {
            "processes": processes,
            "seconds": round(worked, 2),
            "wall_seconds": round(worked_wall, 2),
            "orders_per_second": round(orders / worked, 2) if worked else 0,
            "failed": failed,
            "service_calls": sum(row["calls"] for row in workers),
            "jobs_reported_completed": sum(row["completed"] for row in workers),
        },
        "reservations": {
            "connections": connections,
            "promises": len(promises),
            "seconds": round(reserving, 2),
            "wall_seconds": round(reserving_wall, 2),
            "reserved": sum(row["reserved"] for row in reservers),
            "refused": sum(row["refused"] for row in reservers),
            "per_reservation_ms": round(
                reserving / len(promises) * connections * 1000, 1
            )
            if promises
            else None,
        },
        "target": {
            "orders": TARGET_ORDERS,
            "seconds": TARGET_SECONDS,
            "intake_within_target": orders >= TARGET_ORDERS
            and worked <= TARGET_SECONDS,
            "projected_seconds_for_target": round(worked / orders * TARGET_ORDERS, 1)
            if orders
            else None,
        },
        "checks": checks,
        "environment": {
            "postgresql": postgresql,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cpus": os.cpu_count(),
        },
    }


def _invariants_hold(result: dict[str, Any]) -> bool:
    checks = result["checks"]
    return (
        checks["sales_orders"] == result["orders"]
        and checks["orders_interpreted_more_than_once"] == 0
        and not checks["over_reserved_items"]
        and checks["oversold_matches_demand_less_stock"]
    )


def summary(result: dict[str, Any]) -> str:
    intake, target = result["intake"], result["target"]
    return "\n".join(
        [
            (
                f"orders {result['orders']} · items {result['items']} · "
                f"processes {intake['processes']}"
            ),
            f"store {result['store']['seconds']} s",
            (
                f"intake {intake['seconds']} s · {intake['orders_per_second']} "
                f"orders/s · failed {intake['failed']}"
            ),
            (
                f"projected for {target['orders']} orders: "
                f"{target['projected_seconds_for_target']} s "
                f"(target {target['seconds']} s)"
            ),
            (
                f"reservations {result['reservations']['reserved']} reserved, "
                f"{result['checks']['promises_not_fully_reserved']} not fully "
                f"reserved, in {result['reservations']['seconds']} s"
            ),
            f"invariants {'hold' if _invariants_hold(result) else 'FAIL'}: "
            + json.dumps(
                {
                    key: value
                    for key, value in result["checks"].items()
                    if key != "over_reserved_items"
                }
            ),
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure peak shop intake.")
    parser.add_argument("--orders", type=int, default=TARGET_ORDERS)
    parser.add_argument("--processes", type=int, default=1)
    parser.add_argument("--items", type=int, default=200)
    parser.add_argument("--seed", type=int, default=300)
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    url = os.environ.get("REALITY_DATABASE_URL", "")
    if not url:
        raise ValueError("REALITY_DATABASE_URL is required.")
    validate_database_target(
        make_url(url).database or "", confirmed=args.confirm_disposable
    )
    if "tenant" not in set(inspect(create_engine(url)).get_table_names()):
        raise ValueError("Current Reality schema must be applied before the benchmark.")
    result = run(
        url,
        orders=args.orders,
        processes=args.processes,
        items=args.items,
        seed=args.seed,
    )
    result["git_revision"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()
    args.output.write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(summary(result))
    return 0 if _invariants_hold(result) else 1


if __name__ == "__main__":
    raise SystemExit(main())
