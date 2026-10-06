#!/usr/bin/env python3
"""Synthetic local PostgreSQL Business API load; always owns a disposable database.

This measures HTTP/API reads and bounded rebuild work, not sustained booking capacity.
Use the documented separate scheduler/worker/bookings trial for freshness acceptance.
"""

import argparse
import concurrent.futures
import json
import os
import platform
import statistics
import time
import uuid
from pathlib import Path
from threading import Event, Thread
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session


def percentile(samples: list[float], p: float) -> float:
    return sorted(samples)[min(len(samples) - 1, int(len(samples) * p))]


def shared_freshness(
    engine: Engine,
    tenants: list[str],
    commitments: list[str],
    rounds: int,
    worker_count: int,
) -> dict[str, Any]:
    """Run existing shared roles and confirmed services in this disposable fixture."""
    from reality.db.core import TenantEventProgress, now
    from reality.jobs.runtime import ProcessLoop
    from reality.services import core, projections
    from sqlalchemy import select

    # Warm all shared readers so this probe measures upkeep, not unrelated bootstrap.
    for tenant in tenants:
        with (
            engine.connect().execution_options(
                isolation_level="REPEATABLE READ"
            ) as connection,
            Session(connection) as session,
        ):
            projections.rebuild_projections(
                session, tenant, projections.MATERIALIZED_PROJECTIONS
            )
            session.commit()
    scheduler = ProcessLoop("scheduler")
    workers = [ProcessLoop("worker") for _ in range(worker_count)]
    stop = Event()
    errors = []
    counts = {"scheduler": [], "worker": []}

    def role(loop: ProcessLoop, cadence: float) -> None:
        while not stop.is_set():
            started = time.perf_counter()
            try:
                counts[loop.role].append(
                    loop.sweep(
                        engine,
                        max_runs=100 if loop.role == "scheduler" else 10,
                        max_seconds=25,
                    )
                )
            except Exception as exc:  # noqa: BLE001 - preserve failed probe evidence
                errors.append(type(exc).__name__ + ": " + str(exc))
                stop.set()
            stop.wait(max(0, cadence - (time.perf_counter() - started)))

    threads = [
        Thread(target=role, args=(scheduler, 5)),
        *(Thread(target=role, args=(worker, 1)) for worker in workers),
    ]
    for thread in threads:
        thread.start()
    samples = []
    try:
        anchor = time.perf_counter()
        for n in range(rounds * len(tenants)):
            time.sleep(max(0, anchor + n - time.perf_counter()))
            tenant, promise = tenants[n % len(tenants)], commitments[n % len(tenants)]
            booking_started = time.perf_counter()
            with Session(engine) as session:
                core.revise_commitment(
                    session,
                    tenant,
                    promise,
                    quantity=4 + n,
                    note="Synthetic freshness probe",
                    _commit=False,
                )
                session.commit()
                committed = time.perf_counter()
                sequence = session.scalar(
                    select(TenantEventProgress.last_event_sequence).where(
                        TenantEventProgress.tenant_id == tenant
                    )
                )
            samples.append(
                {
                    "tenant": tenant,
                    "target": sequence,
                    "committed": committed,
                    "committed_at": now().isoformat(),
                    "booking_ms": (committed - booking_started) * 1000,
                    "lag_seconds": None,
                }
            )
            observe_pending(engine, samples)
        deadline = time.perf_counter() + 90
        while (
            any(v["lag_seconds"] is None for v in samples)
            and time.perf_counter() < deadline
            and not errors
        ):
            observe_pending(engine, samples)
            time.sleep(0.1)
    finally:
        stop.set()
        for thread in threads:
            thread.join(timeout=185)
    elapsed = [v["lag_seconds"] for v in samples if v["lag_seconds"] is not None]
    with Session(engine) as session:
        from reality.db.scheduled_jobs import ScheduledJobRun
        from reality.services import business_projection

        remaining = [
            {
                "job_type": run.job_type,
                "status": run.status,
                "names": run.configuration.get("arguments", {}).get("names", []),
            }
            for run in session.scalars(
                select(ScheduledJobRun).where(
                    ScheduledJobRun.status.in_(
                        ["pending", "running", "retrying", "unresolved"]
                    )
                )
            )
        ]
        final_processing = {
            tenant: business_projection.overview(session, tenant)["processing"]
            for tenant in tenants
        }
    return {
        "intended_booking_rate_per_second": 1,
        "actual_booking_rate_per_second": (len(samples) - 1)
        / (samples[-1]["committed"] - samples[0]["committed"])
        if len(samples) > 1
        else None,
        "bookings": len(samples),
        "viewers_during_bookings": 0,
        "scheduler_cadence_seconds": 5,
        "worker_cadence_seconds": 1,
        "worker_processes": worker_count,
        "pending_runs": remaining,
        "final_processing": final_processing,
        "max_runs": {"scheduler": 100, "worker": 10},
        "max_seconds_per_sweep": 25,
        "p95_seconds": percentile(elapsed, 0.95) if elapsed else None,
        "max_seconds": max(elapsed) if elapsed else None,
        "missing": len(samples) - len(elapsed),
        "errors": errors,
        "sweeps": counts,
        "samples": [
            {k: v for k, v in sample.items() if k != "committed"} for sample in samples
        ],
    }


def observe_pending(engine: Engine, samples: list[dict[str, Any]]) -> None:
    from reality.services import business_projection

    for sample in samples:
        if sample["lag_seconds"] is not None:
            continue
        with Session(engine) as session:
            data = business_projection.overview(session, sample["tenant"])
            if (data["processing"]["processed_event_sequence"] or 0) >= sample[
                "target"
            ]:
                sample["lag_seconds"] = time.perf_counter() - sample["committed"]


def run() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orders", type=int, default=10000)
    parser.add_argument("--tenants", type=int, default=3)
    parser.add_argument("--viewers", type=int, default=100)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument(
        "--cadence",
        type=float,
        default=5,
        help="Seconds between viewer polls; zero measures a burst",
    )
    parser.add_argument(
        "--booking-rounds",
        type=int,
        default=0,
        help="Optional ordinary quantity revisions at one booking/second with real shared scheduler/worker subprocesses",
    )
    parser.add_argument("--worker-processes", type=int, default=1)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    if (
        min(args.orders, args.tenants, args.viewers, args.rounds, args.worker_processes)
        < 1
    ):
        parser.error("positive sizes required")
    database = "reality_business_bench_" + uuid.uuid4().hex[:10]
    admin = create_engine(
        "postgresql+psycopg://reality:local-only@127.0.0.1:54329/postgres",
        isolation_level="AUTOCOMMIT",
    )
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database}"'))
    url = f"postgresql+psycopg://reality:local-only@127.0.0.1:54329/{database}"
    engine = create_engine(url, pool_size=20, max_overflow=0, pool_timeout=60)
    os.environ["REALITY_DATABASE_URL"] = url
    os.environ["REALITY_AUTH_MODE"] = "disabled"
    os.environ["REALITY_INTERACTIONS"] = "off"
    from reality.db.core import Base, now
    from reality.services import business_projection, core

    try:
        Base.metadata.create_all(engine)
        tenants = []
        commitments = []
        for t in range(args.tenants):
            with Session(engine) as session:
                tenant = core.create_tenant(session, f"SYNTHETIC Business load {t}")
                tenants.append(tenant.id)
                company = core.create_party(
                    session, tenant.id, "Synthetic company", "company"
                )
                customer = core.create_party(
                    session, tenant.id, "Synthetic customer", "customer"
                )
                item = core.create_item(session, tenant.id, "TEST", "Synthetic item")
                location = core.create_location(
                    session, tenant.id, "Synthetic location"
                )
                source, _, _ = core.store_source_record(
                    session, tenant.id, "benchmark", "order", "sample", {}
                )
                doc = core.create_document(
                    session,
                    tenant.id,
                    "sales_order",
                    "SAMPLE",
                    customer.id,
                    "30",
                    source_record_id=source.id,
                )
                promise = core.create_commitment(
                    session,
                    tenant.id,
                    "customer_delivery",
                    company.id,
                    customer.id,
                    item.id,
                    location.id,
                    3,
                    (now()).isoformat(),
                    document_id=doc.id,
                )
                commitments.append(promise.id)
                session.commit()
                # SQL clones are test-fixture population only; they preserve the
                # shapes created by ordinary services and never touch real tenants.
                document = session.scalar(
                    text(
                        "SELECT to_jsonb(d) FROM document d WHERE tenant_id=:tenant AND id=:id"
                    ),
                    {"tenant": tenant.id, "id": doc.id},
                )
                commitment = session.scalar(
                    text(
                        "SELECT to_jsonb(c) FROM commitment c WHERE tenant_id=:tenant AND document_id=:id"
                    ),
                    {"tenant": tenant.id, "id": doc.id},
                )
                count = args.orders if t == 0 else max(100, args.orders // 10)
                for table, template, overrides in (
                    (
                        "document",
                        document,
                        "jsonb_build_object('id', :prefix || 'd' || g, 'number', 'BENCH-' || g, 'source_record_id', NULL)",
                    ),
                    (
                        "commitment",
                        commitment,
                        "jsonb_build_object('id', :prefix || 'c' || g, 'document_id', :prefix || 'd' || g, 'status', CASE WHEN g%10=0 THEN 'cancelled' ELSE 'open' END)",
                    ),
                ):
                    session.execute(
                        text(
                            f"INSERT INTO {table} SELECT (jsonb_populate_record(NULL::{table}, CAST(:template AS jsonb) || {overrides})).* FROM generate_series(1,:count) g"
                        ),
                        {
                            "template": json.dumps(template),
                            "prefix": f"bench{t}_",
                            "count": count - 1,
                        },
                    )
                session.commit()
        with engine.begin() as connection:
            connection.execute(text("ANALYZE"))
        rebuild = []
        for tenant in tenants:
            units, elapsed = [], time.perf_counter()
            while True:
                started = time.perf_counter()
                with (
                    engine.connect().execution_options(
                        isolation_level="REPEATABLE READ"
                    ) as connection,
                    Session(connection) as session,
                ):
                    business_projection.refresh(session, tenant)
                    session.commit()
                units.append(time.perf_counter() - started)
                with Session(engine) as session:
                    data = business_projection.overview(session, tenant)
                if data["processing"]["state"] == "ready":
                    break
            rebuild.append(
                {
                    "tenant": tenant,
                    "orders": data["order_count"],
                    "seconds": time.perf_counter() - elapsed,
                    "units": len(units),
                    "unit_p95_ms": percentile(units, 0.95) * 1000,
                }
            )
        # ASGI HTTP path includes validation/owner guard in disabled local auth;
        # production cookie/auth overhead and external network are not simulated.
        from fastapi.testclient import TestClient
        from reality.web.app import app

        with TestClient(app) as client:
            warm = client.get(f"/api/tenants/{tenants[0]}/interactions/business")
            assert warm.status_code == 200, warm.text
            poll_anchor = time.perf_counter()

            def viewer(n: int) -> list[float]:
                tenant = tenants[n % len(tenants)]
                samples = []
                for round_no in range(args.rounds):
                    deadline = (
                        poll_anchor + (n / args.viewers + round_no) * args.cadence
                    )
                    time.sleep(max(0, deadline - time.perf_counter()))
                    started = time.perf_counter()
                    response = client.get(
                        f"/api/tenants/{tenant}/interactions/business",
                        params={"order_filter": "blocked" if round_no % 2 else ""},
                    )
                    if response.status_code != 200:
                        raise RuntimeError(
                            f"HTTP {response.status_code}: {response.text[:200]}"
                        )
                    assert response.json()["order_count"] >= 100
                    samples.append((time.perf_counter() - started) * 1000)
                return samples

            started = time.perf_counter()
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=args.viewers
            ) as pool:
                samples = [
                    v for group in pool.map(viewer, range(args.viewers)) for v in group
                ]
        read_seconds = time.perf_counter() - started
        freshness = (
            shared_freshness(
                engine, tenants, commitments, args.booking_rounds, args.worker_processes
            )
            if args.booking_rounds
            else None
        )
        result = {
            "recorded_at": now().isoformat(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "cpu": platform.processor(),
            "visible_cpus": os.cpu_count(),
            "postgres": None,
            "cpu_quota": Path("/sys/fs/cgroup/cpu.max").read_text().strip()
            if Path("/sys/fs/cgroup/cpu.max").exists()
            else "unknown",
            "memory_limit": Path("/sys/fs/cgroup/memory.max").read_text().strip()
            if Path("/sys/fs/cgroup/memory.max").exists()
            else "unknown",
            "workload": vars(args),
            "distribution": "One item/customer/location per company; 90% open unreserved overdue, 10% cancelled; source-less cloned orders; no mail or shipment history.",
            "booking_rate_per_second": 0,
            "viewer_model": f"{args.viewers} ASGI HTTP viewers, phased {args.cadence}s polling; local auth disabled; no network transport",
            "rebuild": rebuild,
            "requests": len(samples),
            "read_seconds": read_seconds,
            "api_p50_ms": statistics.median(samples),
            "api_p95_ms": percentile(samples, 0.95),
            "api_max_ms": max(samples),
            "freshness": freshness,
            "lag_seconds": freshness["p95_seconds"] if freshness else None,
            "lag_reason": "Separate short shared-role probe; no viewers during bookings."
            if freshness
            else "No concurrent booking producer or real scheduler cadence in this read/rebuild benchmark.",
        }
        with engine.connect() as connection:
            result["postgres"] = connection.scalar(text("SELECT version()"))
            result["query_plans"] = {}
            with Session(engine) as session:
                from reality.db.core import ProjectionRow
                from sqlalchemy import select

                state = json.loads(
                    session.scalar(
                        select(ProjectionRow.payload).where(
                            ProjectionRow.tenant_id == tenants[0],
                            ProjectionRow.projection_name == business_projection.NAME,
                            ProjectionRow.record_key == "summary",
                        )
                    )
                )
            for cohort in ("blocked", "complete", "cancelled"):
                result["query_plans"][cohort] = connection.scalar(
                    text(
                        "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) SELECT payload FROM business_order_row "
                        f"WHERE tenant_id=:tenant AND generation=:generation AND flags @> ARRAY['{cohort}']::varchar[] "
                        "ORDER BY received_sort, document_id LIMIT 201"
                    ),
                    {"tenant": tenants[0], "generation": state["active"]},
                )
            result["indexes"] = list(
                connection.execute(
                    text(
                        "SELECT indexname FROM pg_indexes WHERE tablename IN ('business_order_row','business_mail_row') ORDER BY indexname"
                    )
                ).scalars()
            )
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
        print(
            json.dumps(
                {
                    k: result[k]
                    for k in ("requests", "api_p95_ms", "api_max_ms", "rebuild")
                },
                indent=2,
            )
        )
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=:database AND pid <> pg_backend_pid()"
                ),
                {"database": database},
            )
            connection.execute(text(f'DROP DATABASE "{database}"'))
        admin.dispose()


if __name__ == "__main__":
    run()
