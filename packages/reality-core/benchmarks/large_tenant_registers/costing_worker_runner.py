"""Disposable real-queue worker qualification, never normal product startup."""

import argparse
import hashlib
import json
import os
import platform
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import astuple
from pathlib import Path
from threading import Event

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from reality.services import scheduled_jobs as jobs

from .costing_cases import derive
from .costing_dataset import Profile, build, validate
from .costing_generations import (
    initialize,
    published_relation,
    snapshot,
    start_generation,
)
from .costing_runner import digest, summarize, validate_target
from .costing_worker import execute_process, initialize_queue, registered


def reconstruct(engine, *, poll_seconds=5):
    started = time.perf_counter()
    with engine.begin() as c:
        generation = start_generation(c, "a", force=True)
    durations, results = [], []
    stop = Event()

    def reader(index):
        durations, states, generations = [], [], set()
        while not stop.is_set():
            began = time.perf_counter()
            with engine.connect().execution_options(
                isolation_level="REPEATABLE READ"
            ) as c:
                value = snapshot(c, "a", 1 + (index * 7919) % 100000)
                json.dumps(value, default=str)
                states.append(value["state"])
                if value.get("generation"):
                    generations.add(value["generation"])
            durations.append(time.perf_counter() - began)
            stop.wait(0.1)
        return {
            **summarize(durations),
            "states": {s: states.count(s) for s in set(states)},
            "generations": sorted(generations),
        }

    with registered(), ThreadPoolExecutor(max_workers=5) as readers:
        futures = [readers.submit(reader, i) for i in range(5)]
        try:
            for _ in range(100):
                with Session(engine) as session, session.begin():
                    run = jobs.enqueue_projection_run(
                        session, "a", [f"costing:{generation}"]
                    )
                    if run is None:
                        raise AssertionError("Unexpected unfinished fixture run.")
                if poll_seconds:
                    time.sleep(poll_seconds)
                with Session(engine) as session, session.begin():
                    run = jobs.claim_next(session, "a")
                    identity, token = run.id, run.claim_token
                began = time.perf_counter()
                status = execute_process(engine, "a", identity, token)
                durations.append(time.perf_counter() - began)
                if status != "succeeded":
                    raise AssertionError(f"Shared child did not succeed: {status}")
                with engine.connect() as c:
                    result = c.scalar(
                        text(
                            "SELECT result FROM public.scheduled_job_run WHERE tenant_id='a' AND id=:id"
                        ),
                        {"id": identity},
                    )
                results.append(result["counts"])
                if result["counts"]["published"]:
                    break
            else:
                raise AssertionError("Bounded fixture run count exceeded.")
        finally:
            stop.set()
        reads = [f.result() for f in futures]
    elapsed = time.perf_counter() - started
    with engine.connect() as c:
        expected, inventory = derive(c, "a")
        relation = published_relation("a")
        columns = [
            relation.c[k]
            for k in (
                "issue_id",
                "order_id",
                "item",
                "economic_date",
                "cost",
                "revenue",
                "selling",
            )
        ]
        actual = [
            tuple(r) for r in c.execute(select(*columns).order_by(relation.c.issue_id))
        ]
        if actual != sorted(astuple(r) for r in expected):
            raise AssertionError("Published/full replay mismatch.")
        stored_inventory = c.execute(
            text("""SELECT i.item,i.quantity,i.cost,i.unknown_quantity
          FROM costing_spike.generation_inventory i JOIN costing_spike.published_generation p
          ON p.tenant=i.tenant AND p.generation_id=i.generation_id WHERE i.tenant='a' ORDER BY i.item""")
        ).all()
        if [tuple(r) for r in stored_inventory] != sorted(inventory):
            raise AssertionError("Published inventory mismatch.")
        if snapshot(c, "a", 1)["state"] != "ready":
            raise AssertionError("Published revision is not current.")
    return {
        "generation": generation,
        "reconstruction_s": elapsed,
        "children": summarize(durations),
        "job_counts": results,
        "readers": reads,
        "checksum": digest([*actual, *inventory]),
        "observations": len(actual),
        "inventory_pools": len(inventory),
        "poll_seconds": poll_seconds,
        "measured_limits_passed": elapsed <= 120
        and max(durations) < 30
        and all(r["movements"] <= 150000 for r in results),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["reduced", "full"], default="reduced")
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=5)
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.cycles <= 3 or not 0 <= args.poll_seconds <= 5:
        parser.error("Invalid experiment bounds.")
    validate_target(
        os.environ.get("REALITY_DATABASE_URL", ""), confirmed=args.confirm_disposable
    )
    engine = create_engine(
        os.environ["REALITY_DATABASE_URL"], pool_size=8, max_overflow=0
    )
    source_digest = hashlib.sha256(
        b"".join(
            p.read_bytes() for p in sorted(Path(__file__).parent.glob("costing_*.py"))
        )
    ).hexdigest()
    report = {
        "status": "failed",
        "qualification_passed": False,
        "source_digest": source_digest,
    }
    try:
        profile = Profile.named(args.profile)
        started = time.perf_counter()
        with engine.begin() as c:
            tables = c.execute(
                text(
                    "SELECT table_schema,table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')"
                )
            ).all()
            allowed = {"tenant", "app_user", "scheduled_job", "scheduled_job_run"}
            if any(
                schema != "costing_spike"
                and (schema != "public" or name not in allowed)
                for schema, name in tables
            ):
                raise ValueError("Unexpected application tables in experiment target.")
            if tables and not args.reuse:
                raise ValueError("Nonempty target requires validated reuse.")
            if not args.reuse:
                build(c, profile)
                initialize(c)
                initialize_queue(c)
            counts = validate(c, profile)
            if set(c.execute(text("SELECT id FROM public.tenant")).scalars()) != {
                "a",
                "b",
            }:
                raise ValueError("Unexpected control tenant scope.")
        report["setup_s"] = time.perf_counter() - started
        report["cardinalities"] = counts
        report["cycles"] = []
        for i in range(args.cycles):
            result = reconstruct(engine, poll_seconds=args.poll_seconds)
            report["cycles"].append(result)
            print(
                f"generation {i + 1}: {result['reconstruction_s']:.3f}s; child max {result['children']['max_s']:.3f}s",
                flush=True,
            )
        if len({r["checksum"] for r in report["cycles"]}) != 1:
            raise AssertionError("Generation checksum drift.")
        report.update(
            status="exploratory",
            profile=args.profile,
            python=platform.python_version(),
            git_revision=os.environ.get("COSTING_GIT_REVISION")
            or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            elapsed_s=time.perf_counter() - started,
            measured_limits_passed=all(
                r["measured_limits_passed"] for r in report["cycles"]
            ),
            limitations=[
                "Static experimental bootstrap; normal product registry/worker startup remains unchanged.",
                "Real shared queue, child watchdog and settlement; driver simulates five-second worker polling, not deployed scheduler phase/fairness.",
                "Exact dedicated reference host and cold OS cache remain unqualified.",
                "Frozen adjustment revision over immutable v3 base inputs is not general product source-version history.",
                "Typed published SQL relation is exercised; actual analysis compiler/MCP/exception adapters remain unimplemented.",
            ],
        )
        report["process_cgroup"] = {
            name: (Path("/sys/fs/cgroup") / name).read_text().strip()
            for name in ("cpu.max", "memory.max", "memory.swap.max", "memory.peak")
            if (Path("/sys/fs/cgroup") / name).exists()
        }
    except Exception as error:
        report["error_type"] = type(error).__name__
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
        engine.dispose()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
