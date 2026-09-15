"""Process lifecycle; shared services own all scheduling and business behavior."""

from __future__ import annotations

import json
import logging
import math
import os
import signal
from threading import Event
from time import monotonic
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import Engine

from reality.jobs.registry import JobError

logger = logging.getLogger("reality.background")


def database(*, scheduler: bool = False, child: bool = False) -> Engine:
    from sqlalchemy import create_engine, select

    from reality.db.core import resolve_database_url
    from reality.db.scheduled_jobs import ScheduledJob, ScheduledJobRun

    engine = create_engine(
        resolve_database_url(),
        pool_size=1 if child else 2,
        max_overflow=0,
        pool_timeout=2,
        connect_args={
            "connect_timeout": 5,
            "options": f"-c statement_timeout={20000 if child else 2000} -c lock_timeout=2000 -c idle_in_transaction_session_timeout=30000",
        },
    )
    try:
        with engine.connect() as connection:
            connection.execute(select(ScheduledJob).limit(0))
            connection.execute(select(ScheduledJobRun).limit(0))
    except Exception:
        engine.dispose()
        raise
    return engine


class ProcessLoop:
    def __init__(self, role: str, *, tenant_id: str | None = None):
        if role not in ("scheduler", "worker"):
            raise JobError("invalid_role")
        self.role = role
        self.tenant_id = tenant_id
        self.cursor = ""
        self.stop = Event()

    def sweep(self, engine: Engine, *, max_runs: int, max_seconds: float) -> dict:
        import time

        _sweep_started = time.perf_counter()
        from sqlalchemy.orm import Session

        from reality.jobs.runner import execute_process
        from reality.services import scheduled_jobs as jobs

        maximum = 100 if self.role == "scheduler" else 10
        if not 1 <= max_runs <= maximum or not 0 < max_seconds <= 25:
            raise JobError("invalid_budget")
        counts = {
            "materialized": 0,
            "deferred": 0,
            "processed": 0,
            "succeeded": 0,
            "retry": 0,
            "failed": 0,
            "unresolved": 0,
            "budget_exhausted": False,
        }
        deadline = monotonic() + max_seconds
        processed = 0
        while (
            not self.stop.is_set() and monotonic() < deadline and processed < max_runs
        ):
            with Session(engine) as session:
                # The scheduler materializes schedules no run represents yet, so it
                # needs every tenant. A worker only claims runs that already exist
                # (feature 201).
                discover = (
                    jobs.tenant_catalog if self.role == "scheduler" else jobs.due_tenants
                )
                tenants = (
                    [self.tenant_id] if self.tenant_id else discover(session, self.cursor)
                )
            if not tenants:
                self.cursor = ""
                break
            for tenant_id in tenants:
                if (
                    self.stop.is_set()
                    or monotonic() >= deadline
                    or processed >= max_runs
                ):
                    counts["budget_exhausted"] = True
                    break
                self.cursor = tenant_id
                outcomes = {"failed": 0}
                with Session(engine) as session, session.begin():
                    if self.role == "scheduler":
                        from reality.services.projection_jobs import (
                            _prefer_projection,
                            enqueue_due_projections,
                        )

                        result = 0
                        if _prefer_projection(session, tenant_id):
                            result = int(
                                enqueue_due_projections(session, tenant_id) is not None
                            )
                        if result == 0:
                            result = jobs.materialize_due(
                                session, tenant_id, outcomes=outcomes
                            )
                        if result == 0 and not outcomes["failed"]:
                            result = int(
                                enqueue_due_projections(session, tenant_id) is not None
                            )
                        counts["materialized"] += result
                        counts["deferred"] += int(
                            result == 0 and jobs.has_due_schedule(session, tenant_id)
                        )
                        claim = None
                        processed += result
                    else:
                        run = jobs.claim_next(session, tenant_id, outcomes=outcomes)
                        claim = (run.id, run.claim_token) if run else None
                counts["failed"] += outcomes["failed"]
                processed += outcomes["failed"]
                if outcomes["failed"]:
                    logger.warning(
                        json.dumps(
                            {
                                "event": "job_rejected",
                                "role": self.role,
                                "tenant_id": tenant_id,
                                "failed": outcomes["failed"],
                            }
                        )
                    )
                if claim:
                    started = monotonic()
                    status = execute_process(engine, tenant_id, *claim, stop=self.stop)
                    logger.info(
                        json.dumps(
                            {
                                "event": "job_outcome",
                                "tenant_id": tenant_id,
                                "run_id": claim[0],
                                "status": status,
                                "elapsed_seconds": round(monotonic() - started, 3),
                            }
                        )
                    )
                    counts["processed"] += 1
                    if status in counts:
                        counts[status] += 1
                    processed += 1
                # One turn per tenant per sweep; no busy loop on an idle scoped job.
            if counts["budget_exhausted"]:
                break
            if self.tenant_id or len(tenants) < 100:
                self.cursor = ""
                break
        if monotonic() >= deadline or processed >= max_runs:
            counts["budget_exhausted"] = True
        _record_sweep(self.role, counts, time.perf_counter() - _sweep_started)
        return counts

    def run(
        self,
        *,
        continuous: bool,
        poll_seconds: float = 5,
        max_runs: int | None = None,
        max_seconds: float = 25,
    ) -> tuple[dict, int]:
        from sqlalchemy.exc import SQLAlchemyError

        if not math.isfinite(poll_seconds) or poll_seconds < 1:
            raise JobError("invalid_poll_interval")
        max_runs = (
            (100 if self.role == "scheduler" else 10) if max_runs is None else max_runs
        )
        previous = {}
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous[sig] = signal.signal(sig, lambda *_: self.stop.set())
        engine = None
        health_server = None
        failures = 0
        summary = {}
        try:
            port = os.environ.get("REALITY_BACKGROUND_HEALTH_PORT", "")
            if continuous and port:
                from reality.jobs.health import HealthServer

                health_server = HealthServer(self.role, int(port))
                health_server.__enter__()
            engine = database(scheduler=self.role == "scheduler")
            # The runners build their own engine, separate from the web one, so
            # they need instrumenting here or their pool is invisible -- and
            # they are the heaviest sustained DB users in the deployment.
            from reality import telemetry

            telemetry.instrument_engine(engine)
            while not self.stop.is_set():
                try:
                    summary = self.sweep(
                        engine, max_runs=max_runs, max_seconds=max_seconds
                    )
                    failures = 0
                    if health_server:
                        health_server.health.succeeded()
                    logger.info(json.dumps({"event": f"{self.role}_sweep", **summary}))
                    if not continuous:
                        return summary, int(
                            bool(summary["failed"] or summary["unresolved"])
                        )
                except SQLAlchemyError:
                    if health_server:
                        health_server.health.failed()
                    failures += 1
                    logger.error(
                        json.dumps(
                            {
                                "event": f"{self.role}_error",
                                "code": "database_unavailable",
                            }
                        )
                    )
                    if not continuous or failures >= 3:
                        return {"error": "database_unavailable"}, 1
                self.stop.wait(
                    min(poll_seconds, 30) if failures == 0 else min(30, 2**failures)
                )
            return summary, 0
        finally:
            if health_server:
                health_server.__exit__(None, None, None)
            if engine is not None:
                engine.dispose()
            for sig, handler in previous.items():
                signal.signal(sig, handler)


def _record_sweep(role: str, counts: dict, seconds: float) -> None:
    """Publish the sweep counters the runner already computes.

    Wrapped because a metrics fault must never abort a sweep: the job system is
    the thing doing the work, telemetry only describes it.
    """
    try:
        from reality.telemetry.metrics import job_sweep

        job_sweep(role, counts, seconds)
    except Exception:
        logging.getLogger(__name__).debug("sweep metric failed", exc_info=True)
