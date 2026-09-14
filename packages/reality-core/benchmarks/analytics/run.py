"""Disposable PostgreSQL benchmark using ordinary intake, never production records."""

from __future__ import annotations

import argparse
import json
import os
import platform
import time
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.engine import make_url


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=100)
    parser.add_argument("--lines", type=int, default=1000)
    parser.add_argument("--repeat", type=int, default=20)
    parser.add_argument(
        "--resume-database",
        help="Resume only a disposable reality_benchmark_analytics_* database.",
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    admin_url = make_url(
        os.getenv(
            "TEST_POSTGRES_ADMIN_URL",
            "postgresql+psycopg://reality:local-only@localhost:54329/postgres",
        )
    )
    name = args.resume_database or f"reality_benchmark_analytics_{uuid4().hex[:10]}"
    if not name.startswith("reality_benchmark_analytics_"):
        raise ValueError("The resume database must be an analytics benchmark database.")
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    if not args.resume_database:
        with admin.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{name}"'))
    os.environ["REALITY_DATABASE_URL"] = admin_url.set(database=name).render_as_string(
        hide_password=False
    )
    os.environ["REALITY_AUTH_MODE"] = "disabled"
    from reality.db.core import (
        Base,
        Document,
        Item,
        Location,
        Party,
        Session,
        Tenant,
        engine,
    )
    from reality.services.analytics.execution import execute
    from reality.services.core import (
        create_item,
        create_location,
        create_manual_order,
        create_party,
        create_tenant,
    )

    try:
        Base.metadata.create_all(engine)
        with Session() as db:
            tenant = db.scalar(
                select(Tenant).where(Tenant.name == "Analytics benchmark")
            )
            if tenant is None:
                tenant = create_tenant(db, "Analytics benchmark")
                company = create_party(db, tenant.id, "Benchmark company", "company")
                customers = [
                    create_party(db, tenant.id, f"Customer {i}", "customer")
                    for i in range(20)
                ]
                suppliers = [
                    create_party(db, tenant.id, f"Supplier {i}", "supplier")
                    for i in range(10)
                ]
                items = [
                    create_item(db, tenant.id, f"BENCH-{i}", f"Product {i}")
                    for i in range(100)
                ]
                location = create_location(db, tenant.id, "Warehouse")
                start_order = 0
            else:
                parties = {
                    row.name: row
                    for row in db.scalars(
                        select(Party).where(Party.tenant_id == tenant.id)
                    )
                }
                item_by_sku = {
                    row.sku: row
                    for row in db.scalars(
                        select(Item).where(Item.tenant_id == tenant.id)
                    )
                }
                company = parties["Benchmark company"]
                customers = [parties[f"Customer {i}"] for i in range(20)]
                suppliers = [parties[f"Supplier {i}"] for i in range(10)]
                items = [item_by_sku[f"BENCH-{i}"] for i in range(100)]
                location = db.scalar(
                    select(Location).where(
                        Location.tenant_id == tenant.id, Location.name == "Warehouse"
                    )
                )
                start_order = int(
                    db.scalar(
                        select(func.count())
                        .select_from(Document)
                        .where(Document.tenant_id == tenant.id)
                    )
                    or 0
                )
            tenant_id = tenant.id
            started = time.monotonic()
            for i in range(start_order, args.orders):
                direction = "sales" if i < args.orders * 3 // 4 else "purchase"
                counterparty = (
                    customers[i % len(customers)]
                    if direction == "sales"
                    else suppliers[i % len(suppliers)]
                )
                create_manual_order(
                    db,
                    tenant_id,
                    direction,
                    f"BENCH-{i}",
                    company.id,
                    counterparty.id,
                    location.id,
                    [
                        {
                            "item_id": items[j % 100].id,
                            "quantity": "2",
                            "unit_price": "3",
                            "gross_amount": "7",
                            "unit": "pcs",
                        }
                        for j in range(args.lines)
                    ],
                    str(7 * args.lines),
                    ordered_at=f"2026-02-{(i % 28) + 1:02}T10:00:00Z",
                )
                if (i + 1) % 50 == 0:
                    db.commit()
                    print(
                        f"Intake {i + 1}/{args.orders} orders ({time.monotonic() - started:.1f}s)",
                        flush=True,
                    )
            db.commit()
        with engine.connect().execution_options(
            isolation_level="AUTOCOMMIT"
        ) as connection:
            connection.execute(text("ANALYZE"))
            postgres = connection.scalar(text("SELECT version()"))
        cases = [
            {
                "name": "Q01 customer-product-week",
                "definition": {
                    "dataset": "sales_order_lines",
                    "dimensions": ["customer_id"],
                    "measures": ["order_count"],
                    "where": {"field": "product_id", "op": "eq", "value": items[0].id},
                    "time": {
                        "field": "ordered_at",
                        "timezone": "UTC",
                        "window": {"kind": "iso_week", "year": 2026, "week": 7},
                    },
                },
            },
            {
                "name": "Q04 customer-period-change",
                "definition": {
                    "dataset": "sales_orders",
                    "dimensions": ["customer_id"],
                    "measures": ["stated_order_amount"],
                    "time": {
                        "field": "ordered_at",
                        "timezone": "UTC",
                        "window": {
                            "kind": "absolute",
                            "start": "2026-02-15",
                            "end": "2026-03-15",
                        },
                    },
                    "compare": "previous_period",
                },
            },
            {
                "name": "Q06 product-ranking",
                "definition": {
                    "dataset": "sales_order_lines",
                    "dimensions": ["product_id"],
                    "measures": ["ordered_quantity"],
                    "sort": [{"field": "ordered_quantity", "direction": "desc"}],
                },
            },
            {
                "name": "Q07 weekly-products",
                "definition": {
                    "dataset": "sales_order_lines",
                    "dimensions": ["ordered_week", "product_id"],
                    "measures": ["ordered_quantity"],
                },
            },
            {
                "name": "Q08 product-pairs",
                "definition": {
                    "dataset": "order_product_pairs",
                    "dimensions": ["product_id", "product_b_id"],
                    "measures": ["order_count"],
                },
            },
            {
                "name": "Q09 customer-price-range",
                "definition": {
                    "dataset": "sales_order_lines",
                    "dimensions": ["customer_id", "product_id"],
                    "measures": ["min_price", "max_price"],
                },
            },
            {
                "name": "Q22 purchase-price-history",
                "definition": {
                    "dataset": "purchase_order_lines",
                    "dimensions": ["ordered_week", "product_id"],
                    "measures": ["min_price", "max_price"],
                },
            },
            {
                "name": "Q23 supplier-product-history",
                "definition": {
                    "dataset": "purchase_order_lines",
                    "dimensions": ["supplier_id", "product_id"],
                    "measures": ["ordered_quantity", "min_price", "max_price"],
                },
            },
        ]
        runs = []
        captured = {}
        active_case = {"name": None, "iteration": None}

        def capture(_connection, _cursor, statement, parameters, _context, _many):
            lowered = " ".join(statement.lower().split())
            name = active_case["name"]
            if (
                active_case["iteration"] == 0
                and name
                and name not in captured
                and lowered.startswith("select")
                and "analytics_" in lowered
                and " order by " in lowered
            ):
                captured[name] = (statement, parameters.copy())

        event.listen(engine, "before_cursor_execute", capture)
        for iteration in range(args.repeat + 1):
            for case in cases:
                active_case.update(name=case["name"], iteration=iteration)
                definition = case["definition"]
                started = time.monotonic()
                result = execute(tenant_id, {"definition": definition})
                runs.append(
                    {
                        "case": case["name"],
                        "definition": definition,
                        "cache": "first_observation" if iteration == 0 else "warm",
                        "seconds": time.monotonic() - started,
                        "groups": result["page"]["total"],
                    }
                )
                print(json.dumps(runs[-1]), flush=True)
        active_case.update(name=None, iteration=None)
        event.remove(engine, "before_cursor_execute", capture)

        explains = {}
        with engine.connect() as connection:
            for case_name, (statement, parameters) in captured.items():
                plan = connection.exec_driver_sql(
                    "EXPLAIN (FORMAT JSON) " + statement, parameters
                ).scalar()[0]["Plan"]
                nodes = []

                def visit(node, target=nodes):
                    target.append(node["Node Type"])
                    for child in node.get("Plans", []):
                        visit(child)

                visit(plan)
                explains[case_name] = {
                    "total_cost": plan["Total Cost"],
                    "estimated_rows": plan["Plan Rows"],
                    "node_types": nodes,
                    "uses_index": any("Index" in node for node in nodes),
                    "tenant_scope_parameterized": "tenant_id" in statement
                    and bool(parameters),
                }

        def p95(values):
            from math import ceil

            return sorted(values)[ceil(len(values) * 0.95) - 1]

        report = {
            "environment": {"platform": platform.platform(), "postgres": postgres},
            "order_lines": args.orders * args.lines,
            "intake": "create_manual_order",
            "cold_method": "first analytical observation after normal intake and ANALYZE; PostgreSQL/OS caches not flushed",
            "runs": runs,
            "explain": explains,
            "first_p95_seconds": p95(
                [r["seconds"] for r in runs if r["cache"] == "first_observation"]
            ),
            "warm_p95_seconds": p95(
                [r["seconds"] for r in runs if r["cache"] == "warm"]
            ),
        }
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    finally:
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=:name AND pid<>pg_backend_pid()"
                ),
                {"name": name},
            )
            connection.execute(text(f'DROP DATABASE "{name}"'))
        admin.dispose()


if __name__ == "__main__":
    main()
