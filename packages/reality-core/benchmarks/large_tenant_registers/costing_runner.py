"""Disposable costing architecture experiment; reports limits instead of certifying product readiness."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import resource
import statistics
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import astuple
from datetime import date
from pathlib import Path
from queue import Queue
from threading import Event as ThreadEvent

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url

from .costing_cases import (
    attention_read,
    derive,
    inventory_read,
    live_order_read,
    monthly_read,
    observe,
    order_read,
    publish,
    refresh_pool,
    snapshot_read,
)
from .costing_dataset import VERSION, Profile, build, validate
from .runner import validate_database_target


def validate_target(url: str, *, confirmed: bool) -> None:
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql":
        raise ValueError("Only PostgreSQL is supported.")
    validate_database_target(parsed.database or "", confirmed=confirmed, is_empty=True)


def digest(rows) -> str:
    value = hashlib.sha256()
    for r in rows:
        value.update(repr(r).encode())
    return value.hexdigest()


def summarize(samples: list[float]) -> dict:
    values = sorted(samples)
    return {
        "samples": len(values),
        "p50_s": statistics.median(values),
        "p95_s": values[max(0, (95 * len(values) + 99) // 100 - 1)],
        "max_s": max(values),
    }


def workload(
    engine: Engine, name: str, index: int, orders: int, states: list | None = None
) -> float:
    start = time.perf_counter()
    with engine.connect().execution_options(
        isolation_level="REPEATABLE READ"
    ) as connection:

        def read():
            if name in ("order", "tool"):
                value = order_read(connection, "a", (index * 7919) % orders + 1)
                if value is None:
                    raise AssertionError("Ready order disappeared.")
                return value
            if name == "inventory":
                return inventory_read(connection, "a")
            if name == "monthly":
                return monthly_read(
                    connection,
                    "a",
                    date(2024 + (8 + index % 24) // 12, (8 + index % 24) % 12 + 1, 1),
                )
            if name == "attention":
                return attention_read(connection, "a")
            raise ValueError("Unknown workload.")

        if name == "tool":
            # Half the probes deliberately target the last hot-pool order, rather
            # than obtaining apparent availability only from unrelated easy scopes.
            order_id = (
                max(1, orders // 2 - 99)
                if index % 2 == 0
                else (index * 7919) % orders + 1
            )
            response = live_order_read(connection, "a", order_id)
        else:
            response = snapshot_read(connection, "a", read)
        if (
            response["state"] == "current"
            and response.get("assessed_revision", response["published_revision"])
            != response["input_revision"]
        ):
            raise AssertionError("False current state.")
        if states is not None:
            states.append((response["state"], response.get("basis", "projection")))
        json.dumps(response, default=str)
    return time.perf_counter() - start


def run(
    engine: Engine, profile: Profile, strategy: str, samples: int, updates: int
) -> dict:
    result = {
        "strategy": strategy,
        "dataset_version": VERSION,
        "profile": profile.name,
        "qualification_passed": False,
        "measurements": {},
        "limitations": [
            "Exact dedicated 4-vCPU/16-GiB reference host is not certified; see separately captured enforced container limits.",
            "An OS/database cold-cache run and the full freshness response contract are not certified.",
            "Experimental typed relations are not yet wired to the product analysis compiler or exception register.",
            "V3 distributes returns, split/partial matching, supplier credits and stated nonrecoverable tax; full FX/ownership/review and credit-to-revenue matching remain product proofs.",
            "Projection completeness/review invalidation and source-version history are not product implementations.",
        ],
    }
    with engine.connect() as connection:
        result["input_revision_before"] = connection.scalar(
            text(
                "SELECT COALESCE(max(id),0) FROM costing_spike.adjustment WHERE tenant='a'"
            )
        )
    checksums = []
    timings = []
    for iteration in range(3):
        start = time.perf_counter()
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL statement_timeout='120s'"))
            connection.execute(
                text("SELECT id FROM costing_spike.tenant WHERE id='a' FOR UPDATE")
            )
            rows, inventory = derive(connection, "a")
            checksums.append(digest([*rows, *inventory]))
            if strategy == "projection":
                publish(connection, "a", rows, inventory)
        timings.append(time.perf_counter() - start)
        print(f"reconstruction {iteration + 1}: {timings[-1]:.3f}s", flush=True)
        del rows
    if len(set(checksums)) != 1:
        raise AssertionError("Reconstruction checksum drift.")
    result["reconstruction_s"] = timings
    result["checksum"] = checksums[0]
    if strategy == "direct":

        def direct_sample(index: int) -> float:
            started = time.perf_counter()
            with engine.connect() as connection:
                rows = observe(connection, "a", (index * 7919) % profile.orders + 1)
                if len(rows) not in (6, 7):
                    raise AssertionError("Direct order scope incorrect.")
                json.dumps([repr(row) for row in rows])
            return time.perf_counter() - started

        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(direct_sample, range(20)))
            durations = list(pool.map(direct_sample, range(20, 20 + samples)))
        result["measurements"]["order"] = {**summarize(durations), "budget_s": 0.5}
        result["measured_order_budget_passed"] = (
            result["measurements"]["order"]["p95_s"] <= 0.5
        )
        result["limitations"].append(
            "Only direct order latency and whole-pool reconstruction are measured; other direct read surfaces remain unqualified."
        )
        result["input_revision_after"] = result["input_revision_before"]
        return result
    budgets = {"order": 0.5, "tool": 3, "inventory": 2, "monthly": 3, "attention": 2}
    with ThreadPoolExecutor(max_workers=5) as pool:
        for name, budget in budgets.items():
            list(
                pool.map(
                    lambda i, name=name: workload(engine, name, i, profile.orders),
                    range(20),
                )
            )
            values = list(
                pool.map(
                    lambda i, name=name: workload(engine, name, i + 20, profile.orders),
                    range(samples),
                )
            )
            result["measurements"][name] = {**summarize(values), "budget_s": budget}
            print(
                f"{name}: p95 {result['measurements'][name]['p95_s']:.4f}s", flush=True
            )
    # Compare actual direct/projected values rather than timing only a cached constant.
    with engine.connect() as connection:
        for order in (1, profile.orders // 2, profile.orders):
            direct = observe(connection, "a", order)
            stored = order_read(connection, "a", order)
            expected = (
                None
                if any(r.cost is None for r in direct)
                else sum(r.cost for r in direct)
            )
            expected_revenue = (
                None
                if any(r.revenue is None for r in direct)
                else sum(r.revenue for r in direct)
            )
            if stored["cost"] != expected or stored["revenue"] != expected_revenue:
                raise AssertionError("Direct/projected reconciliation failed.")
        if order_read(connection, "foreign", 1) is not None:
            raise AssertionError("Foreign tenant result leaked.")
    refresh = []
    pending = Queue()
    committed_times = []
    changed_counts = []
    mixed_started = time.perf_counter()
    readers_done = ThreadEvent()
    first_commit = ThreadEvent()
    if updates == 0:
        first_commit.set()

    def produce():
        try:
            iteration = 0
            while iteration < updates or (updates > 0 and not readers_done.is_set()):
                delay = mixed_started + iteration - time.perf_counter()
                if delay > 0:
                    time.sleep(delay)
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "SELECT id FROM costing_spike.tenant WHERE id='a' FOR UPDATE"
                        )
                    )
                    connection.execute(
                        text(
                            "INSERT INTO costing_spike.adjustment SELECT 'a',COALESCE(max(id),0)+1,1,0.0001,'source:late:'||(COALESCE(max(id),0)+1) FROM costing_spike.adjustment WHERE tenant='a'"
                        )
                    )
                committed = time.perf_counter()
                committed_times.append(committed - mixed_started)
                pending.put(committed)
                first_commit.set()
                iteration += 1
        finally:
            first_commit.set()
            pending.put(None)

    def worker():
        while (committed := pending.get()) is not None:
            with engine.begin() as connection:
                changed_counts.append(refresh_pool(connection, "a", 1))
            refresh.append(time.perf_counter() - committed)

    def reader(name):
        first_commit.wait()
        values, states = [], []
        read_started = time.perf_counter()
        for index in range(samples):
            delay = (
                mixed_started + index * max(updates, 1) / samples - time.perf_counter()
            )
            if delay > 0:
                time.sleep(delay)
            values.append(workload(engine, name, index + 20, profile.orders, states))
        return {
            **summarize(values),
            "budget_s": budgets[name],
            "started_offset_s": read_started - mixed_started,
            "finished_offset_s": time.perf_counter() - mixed_started,
            "states": {
                state: sum(s[0] == state for s in states)
                for state in sorted({s[0] for s in states})
            },
            "routes": {
                route: sum(s[1] == route for s in states)
                for route in sorted({s[1] for s in states})
            },
        }

    with ThreadPoolExecutor(max_workers=7) as pool:
        producer_future = pool.submit(produce)
        worker_future = pool.submit(worker)
        readers = {name: pool.submit(reader, name) for name in budgets}
        try:
            result["mixed_measurements"] = {
                name: future.result() for name, future in readers.items()
            }
        finally:
            readers_done.set()
        producer_future.result()
        worker_future.result()
    if refresh:
        result["refresh"] = {
            **summarize(refresh),
            "last_affected_rows": changed_counts[-1],
            "requested_minimum_updates": updates,
            "change_stream_covers_all_readers": True,
            "committed_offsets_s": committed_times,
            "one_change_per_second_sustained": all(
                abs(t - i) < 0.25 for i, t in enumerate(committed_times)
            ),
        }
    # Final full replay checks incremental replacement agrees with all retained inputs.
    with engine.connect() as connection:
        direct, inventory = derive(connection, "a")
        stored_rows = connection.execute(
            text(
                "SELECT issue_id,order_id,item,economic_date,cost,revenue,selling FROM costing_spike.observation WHERE tenant='a' ORDER BY issue_id"
            )
        ).all()
        expected = sorted(astuple(r) for r in direct)
        if expected != [tuple(r) for r in stored_rows]:
            raise AssertionError("Incremental/full observation disagreement.")
        stored_inventory = connection.execute(
            text(
                "SELECT item,quantity,cost,unknown_quantity FROM costing_spike.inventory_observation WHERE tenant='a' ORDER BY item"
            )
        ).all()
        if sorted(inventory) != [tuple(r) for r in stored_inventory]:
            raise AssertionError("Incremental/full inventory disagreement.")
        if snapshot_read(connection, "a", lambda: None)["state"] != "current":
            raise AssertionError("Refresh did not reach final input revision.")
        result["reconciliation"] = {
            "observations": len(expected),
            "inventory_pools": len(inventory),
            "complete_values_equal": True,
        }
    result["measured_budgets_passed"] = (
        max(timings) <= 120
        and all(result["measurements"][k]["p95_s"] <= v for k, v in budgets.items())
        and all(
            result["mixed_measurements"][k]["p95_s"] <= v for k, v in budgets.items()
        )
        and (
            not refresh
            or (
                max(refresh) <= 30
                and result["refresh"]["one_change_per_second_sustained"]
            )
        )
    )
    with engine.connect() as connection:
        result["input_revision_after"] = connection.scalar(
            text(
                "SELECT COALESCE(max(id),0) FROM costing_spike.adjustment WHERE tenant='a'"
            )
        )
    if samples < 200 or updates < 30:
        result["limitations"].append(
            "Reduced sample/update counts do not satisfy full fixture J protocol."
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=["reduced", "full"], default="reduced")
    parser.add_argument("--strategy", choices=["direct", "projection"], required=True)
    parser.add_argument("--seed", type=int, choices=[234], default=234)
    parser.add_argument("--business-date", choices=["2026-09-18"], default="2026-09-18")
    parser.add_argument("--confirm-disposable", action="store_true")
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--updates", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.samples < 1 or args.updates < 0:
        parser.error("Positive sample count and nonnegative updates required.")
    url = os.environ.get("REALITY_DATABASE_URL", "")
    validate_target(url, confirmed=args.confirm_disposable)
    engine = create_engine(url, pool_size=7, max_overflow=0)
    profile = Profile.named(args.profile)
    source_digest = hashlib.sha256(
        b"".join(
            p.read_bytes() for p in sorted(Path(__file__).parent.glob("costing_*.py"))
        )
    ).hexdigest()
    started = time.perf_counter()
    report = {"status": "failed", "qualification_passed": False}
    try:
        with engine.begin() as connection:
            # Guard the whole database, not only our namespace, against accidental use.
            tables = connection.scalar(
                text(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema')"
                )
            )
            outside = connection.scalar(
                text(
                    "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema','costing_spike')"
                )
            )
            if outside:
                raise ValueError(
                    "Target contains tables outside the isolated experiment."
                )
            if tables and not args.reuse:
                raise ValueError(
                    "Nonempty database requires validated experiment reuse."
                )
            if not args.reuse:
                build(connection, profile)
            counts = validate(connection, profile)
        setup_duration = time.perf_counter() - started
        report = run(engine, profile, args.strategy, args.samples, args.updates)
        report.update(
            status="exploratory",
            cardinalities=counts,
            setup_s=setup_duration,
            python=platform.python_version(),
            platform=platform.platform(),
            git_revision=os.environ.get("COSTING_GIT_REVISION")
            or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            * (1 if platform.system() == "Darwin" else 1024),
            elapsed_s=time.perf_counter() - started,
        )
        with engine.connect() as connection:
            report["postgres_version"] = connection.scalar(text("SHOW server_version"))
        report["source_digest"] = source_digest
        report["process_cgroup"] = {
            name: (Path("/sys/fs/cgroup") / name).read_text().strip()
            for name in ("cpu.max", "memory.max", "memory.swap.max", "memory.peak")
            if (Path("/sys/fs/cgroup") / name).exists()
        }
        with engine.connect() as connection:
            report["adversarial_distribution"] = dict(
                connection.execute(
                    text(
                        "SELECT kind,count(*) FROM costing_spike.movement WHERE tenant='a' GROUP BY kind"
                    )
                ).all()
            )
    except Exception as error:
        # Avoid leaking connection strings or SQL parameters into committed evidence.
        report["error_type"] = type(error).__name__
        raise
    finally:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, default=str) + "\n")
        engine.dispose()
    print(
        json.dumps(
            {
                "status": report["status"],
                "qualification_passed": False,
                "output": str(args.output),
            },
            indent=2,
        )
    )
    # Exploratory completion is distinct from qualification; never return a green gate.
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
