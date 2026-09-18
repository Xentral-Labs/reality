"""Guarded search dataset and reproducible service workload, never live company data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from http.cookies import SimpleCookie
from pathlib import Path

from fastapi import Response
from sqlalchemy import create_engine, func, insert, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from benchmarks.large_tenant_registers.runner import validate_database_target
from reality.db.analytics import AnalyticsReport
from reality.db.core import (
    AppUser,
    Commitment,
    Document,
    Fact,
    Item,
    LedgerEntry,
    Location,
    Movement,
    Party,
    PartyRole,
    Reservation,
    Shipment,
    ShipmentPackage,
    SourceRecord,
    SubledgerAccount,
    Tenant,
    TenantMembership,
)
from reality.domain.search import SearchRequest
from reality.services.global_search import search_company
from reality.services.memberships import Principal

TENANT = "search_benchmark"
WEIGHTS = {
    "party": 10000,
    "item": 8000,
    "location": 1000,
    "customer_order": 8000,
    "supplier_order": 6000,
    "customer_invoice": 8000,
    "supplier_invoice": 6000,
    "customer_credit": 3000,
    "supplier_credit": 1000,
    "payment": 4000,
    "shipment": 5000,
    "document": 4000,
    "source_record": 10000,
    "commitment": 8000,
    "reservation": 4000,
    "movement": 4000,
    "fact": 4000,
    "ledger_entry": 5000,
    "private_report": 1000,
}
DOCUMENT_TYPES = {
    "customer_order": "sales_order",
    "supplier_order": "purchase_order",
    "customer_invoice": "sales_invoice",
    "supplier_invoice": "supplier_invoice",
    "customer_credit": "credit_note",
    "supplier_credit": "supplier_credit_note",
    "document": "payment",
}


def counts_for(records: int) -> dict[str, int]:
    if records < 1000:
        raise ValueError("The all-family dataset needs at least 1000 records.")
    counts = {key: records * weight // 100000 for key, weight in WEIGHTS.items()}
    counts["item"] += records - sum(counts.values())
    return counts


def seed_database(
    engine, records: int, users: int, seed: int, *, confirmed: bool = False
) -> dict:
    validate_database_target(
        engine.url.database or "", confirmed=confirmed, is_empty=True
    )
    with Session(engine) as guard_session:
        empty = not guard_session.scalar(select(func.count()).select_from(Tenant))
    validate_database_target(
        engine.url.database or "", confirmed=confirmed, is_empty=empty
    )
    counts = counts_for(records)
    if users < 1 or users > counts["private_report"]:
        raise ValueError("The workload needs one private report per user.")
    moment = datetime(2026, 9, 18, 12, tzinfo=UTC)
    names = ["Warehouse", "Müller", "Almacén", "Magazijn"]

    def identity(kind, i):
        return f"bench_{kind}_{i:06}"

    def rows(session, model, values):
        for start in range(0, len(values), 2000):
            session.execute(insert(model), values[start : start + 2000])

    with Session(engine) as session:
        session.add_all(
            [
                Tenant(id=TENANT, name="Search benchmark"),
                Tenant(id="search_other", name="Other benchmark company"),
            ]
        )
        session.flush()
        cookies = []
        for i in range(users):
            actor = AppUser(
                id=f"bench_user_{i}",
                email=f"bench-{seed}-{i}@example.test",
                password_hash="unused-fixture",
                status="active",
                email_verified_at=moment,
            )
            session.add(actor)
            session.flush()
            session.add(
                TenantMembership(
                    id=f"bench_member_{i}",
                    tenant_id=TENANT,
                    user_id=actor.id,
                    role="owner" if i == 0 else "member",
                    status="active",
                )
            )
            from reality.web.auth import create_session

            response = Response()
            create_session(session, actor, response)
            parsed = SimpleCookie()
            parsed.load(response.headers["set-cookie"])
            cookies.append(
                {"user_id": actor.id, "token": parsed["reality_session"].value}
            )
        session.flush()
        rows(
            session,
            Party,
            [
                {
                    "id": identity("party", i),
                    "tenant_id": TENANT,
                    "type": "company",
                    "name": f"{names[(i + seed) % 4]} partner {i:06}",
                    "accounting_code": f"PARTNER-{i:06}",
                }
                for i in range(counts["party"])
            ],
        )
        rows(
            session,
            PartyRole,
            [
                {
                    "id": identity("role", i),
                    "tenant_id": TENANT,
                    "party_id": identity("party", i),
                    "role": "customer" if i % 2 else "supplier",
                }
                for i in range(counts["party"])
            ],
        )
        rows(
            session,
            Item,
            [
                {
                    "id": identity("item", i),
                    "tenant_id": TENANT,
                    "sku": f"SKU-{i:06}",
                    "name": f"{names[(i + seed) % 4]} component {i:06}",
                    "is_active": i % 5 != 0,
                }
                for i in range(counts["item"])
            ],
        )
        rows(
            session,
            Item,
            [
                {
                    "id": "bench_other_item",
                    "tenant_id": "search_other",
                    "sku": "SKU-SECRET",
                    "name": "Other company secret",
                }
            ],
        )
        rows(
            session,
            Location,
            [
                {
                    "id": identity("location", i),
                    "tenant_id": TENANT,
                    "name": f"Warehouse location {i:06}",
                }
                for i in range(counts["location"])
            ],
        )
        rows(
            session,
            SourceRecord,
            [
                {
                    "id": identity("source_record", i),
                    "tenant_id": TENANT,
                    "source_system": "benchmark",
                    "source_type": "order",
                    "external_id": f"EXTERNAL-{i // 2:06}",
                    "version": i % 2 + 1,
                    "payload": "{}",
                    "payload_hash": str(i),
                    "received_at": moment,
                }
                for i in range(counts["source_record"])
            ],
        )
        for family, kind in DOCUMENT_TYPES.items():
            rows(
                session,
                Document,
                [
                    {
                        "id": identity(family, i),
                        "tenant_id": TENANT,
                        "type": kind,
                        "number": f"{family.upper()}-{i:06}",
                        "party_id": identity("party", i % counts["party"]),
                        "source_record_id": identity(
                            "source_record", i % counts["source_record"]
                        ),
                        "gross_amount": 10,
                        "document_date": "2026-09-01",
                    }
                    for i in range(counts[family])
                ],
            )
        rows(
            session,
            Commitment,
            [
                {
                    "id": identity("commitment", i),
                    "tenant_id": TENANT,
                    "type": "customer_delivery",
                    "to_party_id": identity("party", i % counts["party"]),
                    "item_id": identity("item", i % counts["item"]),
                    "location_id": identity("location", 0),
                    "quantity": 1,
                    "document_id": identity(
                        "customer_order", i % counts["customer_order"]
                    ),
                }
                for i in range(counts["commitment"])
            ],
        )
        rows(
            session,
            Reservation,
            [
                {
                    "id": identity("reservation", i),
                    "tenant_id": TENANT,
                    "commitment_id": identity("commitment", i % counts["commitment"]),
                    "item_id": identity("item", i % counts["item"]),
                    "location_id": identity("location", 0),
                    "quantity": 1,
                }
                for i in range(counts["reservation"])
            ],
        )
        rows(
            session,
            Movement,
            [
                {
                    "id": identity("movement", i),
                    "tenant_id": TENANT,
                    "type": "receipt",
                    "item_id": identity("item", i % counts["item"]),
                    "to_location_id": identity("location", 0),
                    "quantity": 1,
                    "source_record_id": identity(
                        "source_record", i % counts["source_record"]
                    ),
                }
                for i in range(counts["movement"])
            ],
        )
        rows(
            session,
            Fact,
            [
                {
                    "id": identity("fact", i),
                    "tenant_id": TENANT,
                    "subject_type": "commitment",
                    "subject_id": identity("commitment", i % counts["commitment"]),
                    "predicate": "benchmark_fixture",
                    "value": '"retained"',
                    "source_record_id": identity(
                        "source_record", i % counts["source_record"]
                    ),
                }
                for i in range(counts["fact"])
            ],
        )
        rows(
            session,
            Shipment,
            [
                {
                    "id": identity("shipment", i),
                    "tenant_id": TENANT,
                    "direction": "outbound",
                    "purpose": "customer_delivery",
                    "counterparty_id": identity("party", i % counts["party"]),
                    "source_record_id": identity(
                        "source_record", i % counts["source_record"]
                    ),
                }
                for i in range(counts["shipment"])
            ],
        )
        rows(
            session,
            ShipmentPackage,
            [
                {
                    "id": identity("package", i),
                    "tenant_id": TENANT,
                    "shipment_id": identity("shipment", i),
                    "tracking_number": f"TRACK-{i:06}",
                }
                for i in range(counts["shipment"])
            ],
        )
        rows(
            session,
            SubledgerAccount,
            [
                {
                    "id": f"bench_account_{role}",
                    "tenant_id": TENANT,
                    "code": role,
                    "name": role,
                    "role": role,
                }
                for role in ["cash", "accounts_receivable"]
            ],
        )
        rows(
            session,
            LedgerEntry,
            [
                {
                    "id": identity("payment", i),
                    "tenant_id": TENANT,
                    "posting_group_id": f"bench_post_{i}",
                    "account_id": "bench_account_cash",
                    "document_id": identity("document", i % counts["document"]),
                    "party_id": identity("party", i % counts["party"]),
                    "amount": 10,
                    "debit_credit": "debit",
                }
                for i in range(counts["payment"])
            ],
        )
        rows(
            session,
            LedgerEntry,
            [
                {
                    "id": identity("ledger_entry", i),
                    "tenant_id": TENANT,
                    "posting_group_id": f"bench_post_{i}",
                    "account_id": "bench_account_accounts_receivable",
                    "document_id": identity("document", i % counts["document"]),
                    "party_id": identity("party", i % counts["party"]),
                    "amount": 10,
                    "debit_credit": "credit",
                }
                for i in range(counts["ledger_entry"])
            ],
        )
        question = {"from": "item", "limit": 20}
        rows(
            session,
            AnalyticsReport,
            [
                {
                    "id": identity("private_report", i),
                    "tenant_id": TENANT,
                    "owner_user_id": f"bench_user_{i % users}",
                    "name": f"Warehouse report {i:06}",
                    "definition": question,
                    "kind": "graph",
                    "model_version": "fixture",
                    "create_request_id": f"create_{i}",
                    "create_payload_hash": str(i),
                    "last_request_id": f"create_{i}",
                    "last_payload_hash": str(i),
                }
                for i in range(counts["private_report"])
            ],
        )
        session.commit()
    with engine.begin() as connection:
        connection.execute(text("ANALYZE"))
    return {
        "tenant": TENANT,
        "records": records,
        "counts": counts,
        "users": cookies,
        "seed": seed,
        "cases": cases_for(counts),
    }


def cases_for(counts):
    return [
        ("partner_exact", "partners", f"PARTNER-{counts['party'] - 1:06}"),
        ("item_exact", "items_locations", f"SKU-{counts['item'] - 1:06}"),
        ("item_prefix", "items_locations", "Warehouse"),
        ("item_typo", "items_locations", "warehose"),
        ("partner_diacritic", "partners", "Muller"),
        ("order_exact", "orders", f"CUSTOMER_ORDER-{counts['customer_order'] - 1:06}"),
        (
            "invoice_exact",
            "finance",
            f"CUSTOMER_INVOICE-{counts['customer_invoice'] - 1:06}",
        ),
        ("payment_exact", "finance", f"bench_payment_{counts['payment'] - 1:06}"),
        ("tracking_exact", "shipping", f"TRACK-{counts['shipment'] - 1:06}"),
        ("source_versions", "reality", "EXTERNAL-000000"),
        ("reality_exact", "reality", f"bench_fact_{counts['fact'] - 1:06}"),
        ("private_reports", "reports", "Warehouse"),
    ]


def run_workload(engine, manifest, observations):
    cases = cases_for(manifest["counts"])

    def measure(task):
        name, provider, query, user, regime = task
        started = time.perf_counter()
        error = None
        hits = 0
        try:
            with Session(engine) as session:
                result = search_company(
                    session,
                    TENANT,
                    Principal(user),
                    SearchRequest(provider=provider, query=query),
                )
                hits = len(result.items)
                if not hits:
                    error = "No expected hit"
        except Exception as exc:  # noqa: BLE001 - every failure remains a timed failed sample
            error = type(exc).__name__
        return {
            "case": name,
            "regime": regime,
            "seconds": time.perf_counter() - started,
            "error": error,
            "hits": hits,
        }

    samples = []
    with ThreadPoolExecutor(max_workers=len(manifest["users"])) as pool:
        for regime, repetitions in [("first_touch", 1), ("warm", observations)]:
            tasks = [
                (
                    name,
                    provider,
                    query,
                    manifest["users"][i % len(manifest["users"])]["user_id"],
                    regime,
                )
                for i in range(repetitions)
                for name, provider, query in cases
            ]
            samples.extend(pool.map(measure, tasks))
    summaries = []
    for regime in ["first_touch", "warm"]:
        for name, _, _ in cases:
            values = [
                sample
                for sample in samples
                if sample["case"] == name and sample["regime"] == regime
            ]
            timings = sorted(row["seconds"] for row in values)
            summaries.append(
                {
                    "case": name,
                    "regime": regime,
                    "observations": len(values),
                    "failures": sum(row["error"] is not None for row in values),
                    "p50": statistics.median(timings),
                    "p95": timings[min(len(timings) - 1, int(len(timings) * 0.95))],
                    "max": max(timings),
                }
            )
    return {
        "summaries": summaries,
        "samples": samples,
        "cold_cache": "Not measured: first_touch does not clear shared PostgreSQL or OS caches.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=int, default=100000)
    parser.add_argument("--users", type=int, default=10)
    parser.add_argument("--seed", type=int, default=235)
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--observations", type=int, default=100)
    parser.add_argument("--seed-only", action="store_true")
    args = parser.parse_args()
    url = os.environ["REALITY_DATABASE_URL"]
    engine = create_engine(url, pool_size=args.users, max_overflow=0)
    with Session(engine) as session:
        empty = not session.scalar(select(func.count()).select_from(Tenant))
    validate_database_target(
        make_url(url).database or "", confirmed=args.confirm_disposable, is_empty=empty
    )
    manifest = seed_database(
        engine, args.records, args.users, args.seed, confirmed=args.confirm_disposable
    )
    manifest_path = args.output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2))
    manifest_path.chmod(0o600)
    evidence = {
        "records": args.records,
        "users": args.users,
        "seed": args.seed,
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "code_digest": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    with engine.connect() as connection:
        evidence["postgresql"] = connection.scalar(text("SELECT version()"))
    if not args.seed_only:
        evidence.update(run_workload(engine, manifest, args.observations))
    args.output.write_text(json.dumps(evidence, indent=2))
    print(
        json.dumps(
            {
                "output": str(args.output),
                "manifest": str(manifest_path),
                "records": args.records,
                "users": args.users,
            }
        )
    )
    return 1 if any(row["failures"] for row in evidence.get("summaries", [])) else 0


if __name__ == "__main__":
    raise SystemExit(main())
