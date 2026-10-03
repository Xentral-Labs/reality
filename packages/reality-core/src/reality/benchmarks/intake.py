"""Qualify exact reviewed intake on an explicitly confirmed disposable database."""

from __future__ import annotations

import argparse
import json
import os
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker


def validate_target(url: str, *, confirmed: bool) -> None:
    if not (make_url(url).database or "").startswith("reality_benchmark_intake_"):
        raise ValueError(
            "Intake qualification requires a disposable benchmark database."
        )
    if not confirmed:
        raise ValueError("Pass --confirm-disposable for the named benchmark database.")


def qualification(trials: list[dict]) -> dict:
    findings = {}
    for workload in sorted({trial["workload"] for trial in trials}):
        selected = [trial for trial in trials if trial["workload"] == workload]
        modes = {
            mode: [trial for trial in selected if trial["mode"] == mode]
            for mode in ("single", "bulk")
        }
        if any(len(rows) != 3 for rows in modes.values()):
            raise ValueError("Each workload needs three measured repetitions per mode.")
        if len({trial["records"] for trial in selected}) != 1:
            raise ValueError("Compared workloads must have equal actual record counts.")
        medians = {
            mode: {
                key: statistics.median(
                    trial["phases"]["apply"][key] / trial["records"] for trial in rows
                )
                for key in ("seconds", "queries")
            }
            for mode, rows in modes.items()
        }
        time_ratio = medians["bulk"]["seconds"] / medians["single"]["seconds"]
        query_ratio = medians["bulk"]["queries"] / medians["single"]["queries"]
        rss = max(trial["incremental_peak_rss_mib"] for trial in selected)
        chunk = max(trial["max_chunk_seconds"] for trial in selected)
        findings[workload] = {
            "medians_per_record": medians,
            "time_ratio": time_ratio,
            "query_ratio": query_ratio,
            "peak_incremental_rss_mib": rss,
            "max_chunk_seconds": chunk,
            "passed": (
                time_ratio <= 1.5
                and query_ratio <= 1.5
                and rss <= 256
                and chunk <= 30
                and all(trial["effects_match"] for trial in selected)
            ),
            "hard_run_bound_passed": chunk <= 120,
        }
    return {
        "passed": bool(findings) and all(row["passed"] for row in findings.values()),
        "workloads": findings,
    }


def run_trial(
    url: str, workload: str, mode: str, *, records: int, confirmed: bool
) -> dict:
    validate_target(url, confirmed=confirmed)
    if workload not in {"orders", "items"} or mode not in {"single", "bulk"}:
        raise ValueError("Unknown controlled workload or decision mode.")
    if not 1 <= records <= (500 if workload == "orders" else 5000):
        raise ValueError("Controlled record count exceeds the qualified workload.")
    from reality.db.core import (
        AppUser,
        ChangeProposal,
        Commitment,
        Document,
        DocumentLine,
        Item,
        TenantMembership,
    )
    from reality.db.scheduled_jobs import ScheduledJobRun
    from reality.services import (
        core,
        intake_batches,
        reviewed_item_imports,
        scheduled_jobs,
    )
    from reality.services.intake import (
        apply_prepared_intake,
        prepare_intake,
        review_intake,
    )
    from reality.services.memberships import Principal

    engine = create_engine(url)
    factory = sessionmaker(engine, expire_on_commit=False)
    phases = {}
    query_count = 0

    def counted(*_arguments):
        nonlocal query_count
        query_count += 1

    @contextmanager
    def phase(name):
        nonlocal query_count
        query_count = 0
        start = time.perf_counter()
        yield
        phases[name] = {"seconds": time.perf_counter() - start, "queries": query_count}

    event.listen(engine, "before_cursor_execute", counted)
    try:
        with (
            factory() as session,
            tempfile.TemporaryDirectory(prefix="intake-volume-") as directory,
        ):
            os.environ["REALITY_ARTIFACT_DIR"] = directory
            tenant = core.create_tenant(session, f"Controlled intake {workload} {mode}")
            owner = AppUser(
                id=core.uid("usr"),
                email=f"{core.uid('mail')}@example.test",
                password_hash="unused",
                status="active",
                email_verified_at=core.now(),
            )
            session.add(owner)
            session.flush()
            session.add(
                TenantMembership(
                    id=core.uid("tmb"),
                    tenant_id=tenant.id,
                    user_id=owner.id,
                    role="owner",
                    status="active",
                )
            )
            company = core.create_party(session, tenant.id, "Volume company", "company")
            customer = core.create_party(
                session, tenant.id, "Volume customer", "customer"
            )
            location = core.create_location(session, tenant.id, "Volume warehouse")
            item = (
                core.create_item(session, tenant.id, "VOLUME-ITEM", "Volume item")
                if workload == "orders"
                else None
            )
            session.commit()
            principal = Principal(owner.id)
            start_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            start_total = time.perf_counter()
            entries = []
            with phase("prepare"):
                if workload == "orders":
                    for index in range(records):
                        payload = {
                            "id": f"volume-{index}",
                            "name": f"Volume {index}",
                            "currency": "EUR",
                            "total_price": "5",
                            "line_items": [
                                {
                                    "id": f"line-{line}",
                                    "sku": item.sku,
                                    "name": "Received item",
                                    "quantity": 1,
                                    "price": "1",
                                    "total_price": "1",
                                }
                                for line in range(5)
                            ],
                        }
                        _, job = core.enqueue_shopify_order(
                            session,
                            tenant.id,
                            payload,
                            company.id,
                            customer.id,
                            location.id,
                        )
                        proposal = prepare_intake(session, tenant.id, job.id)
                        entries.append(
                            {
                                "proposal_id": proposal.id,
                                "digest": json.loads(proposal.input)["digest"],
                            }
                        )
                    batch = intake_batches.prepare_batch(
                        session, tenant.id, entries, request_id="volume-selection"
                    )
                else:
                    content = (
                        "sku,name\n"
                        + "".join(
                            f"ITEM-{index},Received item {index}\n"
                            for index in range(records)
                        )
                    ).encode()
                    staged = reviewed_item_imports.stage_reviewed_item_csv(
                        session, tenant.id, content, "volume.csv"
                    )
                    prepared = reviewed_item_imports.prepare_reviewed_item_file(
                        session,
                        tenant.id,
                        staged["source_record_id"],
                        {"sku": "sku", "name": "name"},
                        request_id="volume-selection",
                    )
                    entries = prepared["entries"]
                    batch = session.get(
                        ChangeProposal, (tenant.id, prepared["batch_id"])
                    )
            with phase("review"):
                for entry in entries:
                    held = review_intake(session, tenant.id, entry["proposal_id"])
                    assert held["digest"] == entry["digest"]
                intake_batches.review_batch(session, tenant.id, batch.id)
            chunks = []
            with phase("apply"):
                if mode == "single":
                    for entry in entries:
                        started = time.perf_counter()
                        apply_prepared_intake(
                            session,
                            tenant.id,
                            entry["proposal_id"],
                            entry["digest"],
                            confirmed=True,
                            principal=principal,
                        )
                        chunks.append(time.perf_counter() - started)
                else:
                    intake_batches.approve_batch(
                        session,
                        tenant.id,
                        batch.id,
                        json.loads(batch.input)["digest"],
                        confirmed=True,
                        principal=principal,
                    )
                    while batch.status != "executed":
                        started = time.perf_counter()
                        claim = scheduled_jobs.claim_next(session, tenant.id)
                        if claim is None:
                            raise RuntimeError(
                                "An approved batch has no claimable continuation."
                            )
                        run_id, claim_token = claim.id, claim.claim_token
                        session.commit()
                        assert (
                            scheduled_jobs.execute_claim(
                                session, tenant.id, run_id, claim_token
                            )
                            == "succeeded"
                        )
                        session.commit()
                        session.refresh(batch)
                        chunks.append(time.perf_counter() - started)
            measured_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

            def count(model):
                return session.scalar(
                    select(func.count())
                    .select_from(model)
                    .where(model.tenant_id == tenant.id)
                )

            counts = {
                "documents": count(Document),
                "lines": count(DocumentLine),
                "commitments": count(Commitment),
                "items": count(Item),
            }
            accepted = list(
                session.scalars(
                    select(ChangeProposal).where(
                        ChangeProposal.tenant_id == tenant.id,
                        ChangeProposal.type == "tool:intake_apply",
                    )
                )
            )
            effects_match = all(
                row.status == "executed" and row.decided_by_user_id == owner.id
                for row in accepted
            ) and len(accepted) == len(entries)
            if workload == "orders":
                effects_match &= counts == {
                    "documents": records,
                    "lines": records * 5,
                    "commitments": records * 5,
                    "items": 1,
                }
            else:
                effects_match &= counts == {
                    "documents": 0,
                    "lines": 0,
                    "commitments": 0,
                    "items": records,
                }
            status = intake_batches.batch_status(session, tenant.id, batch.id)
            if mode == "bulk":
                effects_match &= status["counts"] == {"applied": len(entries)}
            runs = list(
                session.scalars(
                    select(ScheduledJobRun).where(
                        ScheduledJobRun.tenant_id == tenant.id,
                        ScheduledJobRun.job_type == "intake.batch_apply",
                    )
                )
            )
            config_bytes = max(
                (len(json.dumps(run.configuration).encode()) for run in runs), default=0
            )
            result_bytes = max(
                (len(json.dumps(run.result).encode()) for run in runs if run.result),
                default=0,
            )
            if mode == "bulk":
                effects_match &= bool(runs) and all(
                    run.status == "succeeded" for run in runs
                )
            return {
                "workload": workload,
                "mode": mode,
                "records": records,
                "units": len(entries),
                "counts": counts,
                "effects_match": bool(effects_match),
                "phases": phases,
                "total_seconds": time.perf_counter() - start_total,
                "max_chunk_seconds": max(chunks),
                "chunk_seconds": chunks,
                "incremental_peak_rss_mib": max(0, measured_rss - start_rss) / 1024,
                "peak_rss_mib": measured_rss / 1024,
                "queue_config_bytes": config_bytes,
                "queue_result_bytes": result_bytes,
                "actual_worker_runs": len(runs),
            }
    finally:
        event.remove(engine, "before_cursor_execute", counted)
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url", default=os.environ.get("REALITY_DATABASE_URL")
    )
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument("--baseline-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trial", action="store_true")
    parser.add_argument("--workload", choices=("items", "orders"))
    parser.add_argument("--mode", choices=("single", "bulk"))
    parser.add_argument("--records", type=int)
    args = parser.parse_args()
    if not args.database_url:
        parser.error("A disposable database URL is required.")
    validate_target(args.database_url, confirmed=args.confirm_disposable)
    if args.trial:
        result = run_trial(
            args.database_url,
            args.workload,
            args.mode,
            records=args.records,
            confirmed=args.confirm_disposable,
        )
        args.output.write_text(json.dumps(result, indent=2) + "\n")
        return
    trials, warmups = [], []
    for workload, records in (("orders", 500), ("items", 5000)):
        for mode in ("single", "bulk"):
            for repetition in range(4):
                with tempfile.TemporaryDirectory(
                    prefix="intake-measurement-"
                ) as directory:
                    output = Path(directory) / "trial.json"
                    subprocess.run(
                        [
                            sys.executable,
                            "-m",
                            "reality.benchmarks.intake",
                            "--confirm-disposable",
                            "--baseline-commit",
                            args.baseline_commit,
                            "--output",
                            str(output),
                            "--trial",
                            "--workload",
                            workload,
                            "--mode",
                            mode,
                            "--records",
                            str(records),
                        ],
                        env={**os.environ, "REALITY_DATABASE_URL": args.database_url},
                        check=True,
                    )
                    trial = json.loads(output.read_text())
                (warmups if repetition == 0 else trials).append(trial)
                print(
                    f"{workload} {mode} repetition={repetition} seconds={trial['total_seconds']:.2f}",
                    flush=True,
                )
    engine = create_engine(args.database_url)
    with engine.connect() as connection:
        version = connection.scalar(text("SHOW server_version"))
    engine.dispose()
    result = {
        "baseline_commit": args.baseline_commit,
        "host": platform.platform(),
        "cpu_count": os.cpu_count(),
        "postgresql": version,
        "topology": "local PostgreSQL",
        "reviewer": "controlled confirmed owner; no provider/model quality claim",
        "warmups": warmups,
        "trials": trials,
        "qualification": qualification(trials),
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if not result["qualification"]["passed"]:
        raise SystemExit("Measured intake qualification exceeded a declared budget.")


if __name__ == "__main__":
    main()
