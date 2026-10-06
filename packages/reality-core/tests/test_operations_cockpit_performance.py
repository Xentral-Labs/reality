"""Reproducible isolated enterprise read profile; never seed a real company.

Bulk rows model already accepted historical data, not a second production intake.
Planning acceptance and subsequent fixture changes use canonical shared services.
"""

import cProfile
import hashlib
import json
import math
import os
import platform
import time
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import event, func, insert, select, text
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    Commitment,
    DatabasePoolSettings,
    Document,
    Movement,
    Reservation,
    Shipment,
    ShipmentEvent,
    ShipmentPackage,
    SourceRecord,
    build_engine,
)
from reality.db.operational_cases import OperationalCase
from reality.services import core, operations_cockpit
from reality.services.memberships import Principal
from reality.tools.application import (
    approve_and_execute_proposal,
    create_change_proposal,
)


def _bulk(db, model, rows):
    chunk = []
    for row in rows:
        chunk.append(row)
        if len(chunk) == 2000:
            db.execute(insert(model), chunk)
            chunk = []
    if chunk:
        db.execute(insert(model), chunk)


@pytest.fixture
def enterprise_database(scheduled_database):
    base, _, tenant, owner = scheduled_database
    # Ten browsers may issue four independent reads, each with caller authority
    # plus an isolated snapshot. This uses existing bounded deployment settings.
    engine = build_engine(
        base.url.render_as_string(hide_password=False),
        pool_settings=DatabasePoolSettings(pool_size=80, max_overflow=5),
    )
    try:
        yield engine, sessionmaker(engine, expire_on_commit=False), tenant, owner
    finally:
        engine.dispose()


def test_ten_reader_enterprise_profile_preserves_full_totals_and_refresh_latency(
    enterprise_database, monkeypatch
):
    # BUSINESS PURPOSE: Enterprise claims require measured complete observations, not a small fixture screenshot.
    # BUSINESS RULE: Ten fresh observers retain independent semantic totals and see an actual committed change.
    engine, factory, tenant, owner = enterprise_database
    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    observed = datetime.now(UTC)
    day = observed.date().isoformat()
    start = observed.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    historical = start - timedelta(days=30)
    with factory() as db:
        company = core.create_party(db, tenant, "Performance Company", "company")
        customer = core.create_party(db, tenant, "Performance Customer", "customer")
        item = core.create_item(db, tenant, "PERF-378", "Performance item")
        locations = [
            core.create_location(db, tenant, code, code) for code in ("A", "B")
        ]
        source, _, _ = core.store_source_record(
            db,
            tenant,
            "performance-fixture",
            "accepted-orders",
            "batch",
            {
                "profile": "110000 accepted orders, one-unit mix",
                "active": 10000,
                "historical": 100000,
            },
        )

        def original_orders():
            for i in range(110000):
                payload = json.dumps(
                    {"number": f"PERF-{i}", "quantity": "1", "gross_amount": "1"},
                    sort_keys=True,
                )
                yield {
                    "tenant_id": tenant,
                    "id": f"perf_source_{i:06}",
                    "source_system": "performance-fixture",
                    "source_type": "accepted-order",
                    "external_id": f"order-stream-{i}",
                    "version": 1,
                    "payload": payload,
                    "payload_hash": hashlib.sha256(payload.encode()).hexdigest(),
                    "received_at": observed if i < 10000 else historical,
                }

        _bulk(db, SourceRecord, original_orders())
        _bulk(
            db,
            Document,
            (
                {
                    "tenant_id": tenant,
                    "id": f"perf_order_{i:06}",
                    "type": "sales_order",
                    "number": f"PERF-{i}",
                    "party_id": customer.id,
                    "source_record_id": f"perf_source_{i:06}",
                    "gross_amount": "1",
                }
                for i in range(110000)
            ),
        )
        _bulk(
            db,
            Commitment,
            (
                {
                    "tenant_id": tenant,
                    "id": f"perf_commitment_{i:06}",
                    "type": "customer_delivery",
                    "from_party_id": company.id,
                    "to_party_id": customer.id,
                    "item_id": item.id,
                    "location_id": locations[i % 2].id,
                    "quantity": "1",
                    "status": "open" if 1000 <= i < 10000 else "fulfilled",
                    "document_id": f"perf_order_{i:06}",
                    "created_at": observed if i < 10000 else historical,
                }
                for i in range(110000)
            ),
        )
        fulfilled = [*range(1000), *range(10000, 110000)]
        _bulk(
            db,
            Shipment,
            (
                {
                    "tenant_id": tenant,
                    "id": f"perf_shipment_{i:06}",
                    "direction": "outbound",
                    "purpose": "customer_delivery",
                    "counterparty_id": customer.id,
                    "source_record_id": source.id,
                    "created_at": observed if i < 10000 else historical,
                }
                for i in fulfilled
            ),
        )
        _bulk(
            db,
            ShipmentPackage,
            (
                {
                    "tenant_id": tenant,
                    "id": f"perf_package_{i:06}",
                    "shipment_id": f"perf_shipment_{i:06}",
                    "source_record_id": source.id,
                }
                for i in fulfilled
            ),
        )
        for loc in locations:
            core.record_movement(
                db,
                tenant,
                "receipt",
                item.id,
                "60000",
                to_location_id=loc.id,
                occurred_at=historical,
            )
        _bulk(
            db,
            Movement,
            (
                {
                    "tenant_id": tenant,
                    "id": f"perf_movement_{i:06}",
                    "type": "shipment",
                    "item_id": item.id,
                    "quantity": "1",
                    "from_location_id": locations[i % 2].id,
                    "commitment_id": f"perf_commitment_{i:06}",
                    "shipment_package_id": f"perf_package_{i:06}",
                    "source_record_id": source.id,
                    "occurred_at": observed - timedelta(minutes=1)
                    if i < 10000
                    else historical,
                }
                for i in fulfilled
            ),
        )
        _bulk(
            db,
            Reservation,
            (
                {
                    "tenant_id": tenant,
                    "id": f"perf_reservation_{i:06}",
                    "commitment_id": f"perf_commitment_{i:06}",
                    "item_id": item.id,
                    "location_id": locations[i % 2].id,
                    "quantity": "1",
                    "status": "active",
                }
                for i in range(1000, 10000)
            ),
        )
        _bulk(
            db,
            ShipmentEvent,
            (
                {
                    "tenant_id": tenant,
                    "id": f"perf_observation_{index:06}",
                    "shipment_id": f"perf_shipment_{fulfilled[index % len(fulfilled)]:06}",
                    "event_type": "handed_over",
                    "reporter_type": "carrier",
                    "occurred_at": observed - timedelta(seconds=30)
                    if fulfilled[index % len(fulfilled)] < 10000
                    else historical,
                    "source_record_id": source.id,
                }
                for index in range(500000)
            ),
        )
        db.commit()
        for index, loc in enumerate(locations):
            confirmation, _, _ = core.store_source_record(
                db,
                tenant,
                "performance-fixture",
                "capacity",
                loc.id,
                {
                    "unit": "site-cohort order completion",
                    "completion_slots": 5000,
                    "mix": "one-unit orders",
                },
            )
            plan = {
                "business_day": day,
                "business_time_zone": "UTC",
                "dispatch_location_id": loc.id,
                "site_time_zone": "UTC",
                "requirements": [
                    {
                        "commitment_id": f"perf_commitment_{i:06}",
                        "quantity": "1",
                        "dispatch_due_at": (end - timedelta(seconds=1)).isoformat(),
                        "planned_handover_at": (end - timedelta(minutes=1)).isoformat(),
                    }
                    for i in range(index, 10000, 2)
                ],
                "capacity_windows": [
                    {
                        "starts_at": observed.isoformat(),
                        "ends_at": (end - timedelta(seconds=2)).isoformat(),
                        "collection_cutoff_at": (
                            end - timedelta(seconds=2)
                        ).isoformat(),
                        "completion_slots": 5000,
                        "confirmation_state": "confirmed",
                        "confirmation_source_record_id": confirmation.id,
                    }
                ],
            }
            proposal = create_change_proposal(
                db, tenant, "shipping_plan_state", {"plan": plan}
            )
            approve_and_execute_proposal(
                db,
                tenant,
                proposal.id,
                confirming_principal=Principal(owner),
                confirmed=True,
            )
        # Canonical plan acceptance already binds its supported cases by default.
        # Seed only the remaining accepted-history fixture cases; preserve those
        # actual identities and links instead of duplicating their order scope.
        bound_orders = set(
            db.scalars(
                select(OperationalCase.order_document_id).where(
                    OperationalCase.tenant_id == tenant
                )
            )
        )
        _bulk(
            db,
            OperationalCase,
            (
                {
                    "tenant_id": tenant,
                    "id": f"perf_case_{i:06}",
                    "kind": "order_fulfillment",
                    "order_document_id": f"perf_order_{i:06}",
                    "control_mode": "automation",
                    "created_at": observed if i < 10000 else historical,
                }
                for i in range(110000)
                if f"perf_order_{i:06}" not in bound_orders
            ),
        )
        assert (
            db.scalar(
                select(func.count())
                .select_from(OperationalCase)
                .where(OperationalCase.tenant_id == tenant)
            )
            == 110000
        )
        db.execute(text("ANALYZE"))
        db.commit()
    with factory() as metadata:
        postgres = dict(
            metadata.execute(
                text(
                    "SELECT version() AS version, current_setting('shared_buffers') AS shared_buffers, "
                    "current_setting('work_mem') AS work_mem, current_setting('max_connections') AS max_connections, "
                    "current_setting('max_parallel_workers_per_gather') AS max_parallel_workers_per_gather"
                )
            )
            .one()
            ._mapping
        )
    memory_bytes = (
        os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")
        if "SC_PHYS_PAGES" in os.sysconf_names
        else None
    )
    samples = []
    query_counts = []
    payload_bytes = []
    query_count = ContextVar("cockpit_profile_query_count", default=0)

    def record_query(*args):
        query_count.set(query_count.get() + 1)

    event.listen(engine, "before_cursor_execute", record_query)

    def read(index):
        query_count.set(0)
        began = time.perf_counter()
        with factory() as db:
            value = operations_cockpit.operations_cockpit(
                db,
                tenant,
                Principal(owner),
                day=day,
                location_id=locations[index % 2].id if index >= 10 else None,
            )
            assert value["shipping"]["totals"] == {
                "due": 5000 if index >= 10 else 10000,
                "handed_over": 500 if index >= 10 else 1000,
                "forecast": 5000 if index >= 10 else 10000,
                "risk": 0,
            }
            assert value["supported_cases"]["counts"]["completed"] == 101000
            assert value["supported_cases"]["counts"]["outstanding"] == 9000
        payload = json.dumps(value).encode()
        return time.perf_counter() - began, query_count.get(), len(payload)

    cold, cold_queries, cold_bytes = read(0)
    if os.environ.get("REALITY_COCKPIT_PROFILE") == "1":
        diagnostic_queries = []

        def query_started(connection, cursor, statement, parameters, context, many):
            context._cockpit_diagnostic_started = time.perf_counter()

        def query_finished(connection, cursor, statement, parameters, context, many):
            if statement.lstrip().upper().startswith("SELECT"):
                diagnostic_queries.append(
                    (
                        time.perf_counter() - context._cockpit_diagnostic_started,
                        statement,
                        parameters,
                    )
                )

        event.listen(engine, "before_cursor_execute", query_started)
        event.listen(engine, "after_cursor_execute", query_finished)
        profiler = cProfile.Profile()
        try:
            profiler.runcall(read, 0)
        finally:
            event.remove(engine, "before_cursor_execute", query_started)
            event.remove(engine, "after_cursor_execute", query_finished)
        profiler.dump_stats("/private/tmp/reality-378-cold-profile.pstats")
        # Diagnostic-only, before concurrency or business changes. Never retain
        # parameters/source payloads in the output or alter acceptance samples.
        plans = []
        with engine.connect() as connection:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            for duration, statement, parameters in sorted(
                diagnostic_queries, key=lambda row: row[0], reverse=True
            )[:12]:
                plan = connection.exec_driver_sql(
                    "EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + statement,
                    parameters,
                ).scalar_one()[0]

                def summarize(node):
                    return {
                        key: value
                        for key, value in node.items()
                        if key
                        in {
                            "Node Type",
                            "Relation Name",
                            "Index Name",
                            "Plan Rows",
                            "Actual Rows",
                            "Actual Loops",
                            "Actual Total Time",
                            "Shared Hit Blocks",
                            "Shared Read Blocks",
                            "Temp Read Blocks",
                            "Temp Written Blocks",
                        }
                    } | {"Plans": [summarize(child) for child in node.get("Plans", [])]}

                plans.append(
                    {
                        "observed_seconds": duration,
                        "statement": statement,
                        "execution_ms": plan["Execution Time"],
                        "planning_ms": plan["Planning Time"],
                        "plan": summarize(plan["Plan"]),
                    }
                )
        from pathlib import Path

        Path("/private/tmp/reality-378-cold-query-plans.json").write_text(
            json.dumps(plans, indent=2)
        )
    print(
        json.dumps(
            {
                "cold_seconds": cold,
                "cold_queries": cold_queries,
                "cold_payload_bytes": cold_bytes,
            }
        ),
        flush=True,
    )
    with ThreadPoolExecutor(max_workers=10) as pool:
        for indexes in (range(10), range(10, 20)):
            for elapsed, queries, size in pool.map(read, indexes):
                samples.append(elapsed)
                query_counts.append(queries)
                payload_bytes.append(size)
    with factory() as writer:
        before = time.monotonic()
        core.hold_commitment(
            writer,
            tenant,
            "perf_commitment_001000",
            "customer_request",
            "Committed live fixture change",
        )
    with factory() as reader:
        changed = operations_cockpit.operations_cockpit(
            reader, tenant, Principal(owner), day=day
        )
        assert changed["shipping"]["totals"]["risk"] == 1
        assert changed["shipping"]["totals"]["forecast"] == 9999
    commit_to_observation = time.monotonic() - before
    p95 = sorted(samples)[math.ceil(len(samples) * 0.95) - 1]
    print(
        json.dumps(
            {
                "hardware": platform.platform(),
                "python": platform.python_version(),
                "cpu_count": os.cpu_count(),
                "memory_bytes": memory_bytes,
                "postgres": postgres,
                "pool_size": 80,
                "max_overflow": 5,
                "query_counts": query_counts,
                "payload_bytes": payload_bytes,
                "cold_method": "First application read after fixture ANALYZE; PostgreSQL OS/shared buffers are not flushed.",
                "active": 10000,
                "historical": 100000,
                "shipment_observations": 500000,
                "readers": 10,
                "cold_seconds": cold,
                "samples": samples,
                "p95_seconds": p95,
                "commit_to_observation_seconds": commit_to_observation,
                "distribution": "Two sites, one item, partial-allowed EUR orders, 1000 complete active, 9000 ready active, 100000 fulfilled historical, no prepayment; exact canonical owner-reviewed plans.",
            }
        )
    )
    assert max([cold_queries, *query_counts]) <= 250
    assert p95 <= 3, p95
    assert commit_to_observation <= 10, commit_to_observation

    live_samples = []
    cycle_samples = []
    write_samples = []
    live_queries = []
    live_payload_bytes = []

    def live_read(kind, epoch):
        query_count.set(0)
        began = time.monotonic()
        with factory() as db:
            if kind == "overview":
                value = operations_cockpit.operations_cockpit(
                    db, tenant, Principal(owner), day=day
                )
                assert value["shipping"]["totals"]["due"] == 10000
                assert value["shipping"]["totals"]["risk"] == 1
                assert value["shipping"]["totals"]["forecast"] == 9999
                assert (
                    9000 + epoch - 1
                    <= value["supported_cases"]["counts"]["outstanding"]
                    <= 9000 + epoch
                )
            elif kind == "register":
                value = operations_cockpit.case_register(
                    db, tenant, Principal(owner), limit=6, outstanding_only=True
                )
                assert value["counts"]["completed"] == 101000
                assert (
                    9000 + epoch - 1 <= value["counts"]["outstanding"] <= 9000 + epoch
                )
            elif kind == "activity":
                value = operations_cockpit.activity(
                    db, tenant, Principal(owner), minutes=15
                )
                assert value["counts"].get("orders", 0) >= epoch - 1
                assert len(value["buckets"]) <= 61 and len(value["events"]) <= 50
            else:
                value = operations_cockpit.agents(db, tenant, Principal(owner), limit=6)
                assert value["total"] == 0
            payload = json.dumps(value).encode()
        return time.monotonic() - began, query_count.get(), len(payload)

    def live_write(epoch):
        began = time.monotonic()
        with factory() as writer:
            core.create_manual_order(
                writer,
                tenant,
                "sales",
                f"LIVE-{epoch}",
                company.id,
                customer.id,
                locations[0].id,
                [
                    {
                        "item_id": item.id,
                        "quantity": "1",
                        "unit_price": "1",
                        "gross_amount": "1",
                    }
                ],
                "1",
            )
        return time.monotonic() - began, time.monotonic()

    # Source changes arrive while browsers read, not before a serialized batch.
    # Each consistent observation may precede or follow this cycle's commit;
    # every next-cycle read must include the previously committed order.
    with (
        ThreadPoolExecutor(max_workers=40) as live_pool,
        ThreadPoolExecutor(max_workers=1) as write_pool,
    ):
        for epoch in range(1, 13):
            cycle_started = time.monotonic()
            write_future = write_pool.submit(live_write, epoch)
            futures = [
                live_pool.submit(live_read, kind, epoch)
                for _ in range(10)
                for kind in ("overview", "register", "activity", "agents")
            ]
            for future in futures:
                elapsed, queries, size = future.result()
                live_samples.append(elapsed)
                live_queries.append(queries)
                live_payload_bytes.append(size)
            assert max(live_queries[-40:]) <= 250
            write_elapsed, last_commit_at = write_future.result()
            write_samples.append(write_elapsed)
            elapsed = time.monotonic() - cycle_started
            cycle_samples.append(elapsed)
            print(
                json.dumps(
                    {
                        "epoch": epoch,
                        "cycle_seconds": elapsed,
                        "write_seconds": write_samples[-1],
                        "read_p95_seconds": sorted(live_samples[-40:])[37],
                    }
                ),
                flush=True,
            )
            assert elapsed <= 5, (
                "The ten-browser foreground cadence overruns",
                epoch,
                elapsed,
            )
            if elapsed < 5:
                time.sleep(5 - elapsed)
    with factory() as reader:
        final_register = operations_cockpit.case_register(
            reader, tenant, Principal(owner), limit=6, outstanding_only=True
        )
        assert final_register["counts"]["outstanding"] == 9012
    final_visibility = time.monotonic() - last_commit_at
    assert final_visibility <= 10, final_visibility
    live_p95 = sorted(live_samples)[math.ceil(len(live_samples) * 0.95) - 1]
    print(
        json.dumps(
            {
                "live_seconds": 60,
                "live_requests": len(live_samples),
                "live_p95_seconds": live_p95,
                "live_max_queries": max(live_queries),
                "live_max_payload_bytes": max(live_payload_bytes),
                "cycle_seconds": cycle_samples,
                "write_seconds": write_samples,
                "committed_new_orders": 12,
                "last_commit_to_verified_observation_seconds": final_visibility,
                "writer_mode": "Concurrent canonical writer; old/new exact snapshot parity and mandatory next-cycle visibility",
            }
        ),
        flush=True,
    )
    assert live_p95 <= 3, live_p95
