from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

from sqlalchemy import func, select
from test_scheduled_invitation_cleanup import invitation

from reality.db.core import CompanyInvitation, now
from reality.db.scheduled_jobs import ScheduledJobRun
from reality.jobs.runtime import ProcessLoop
from reality.services import scheduled_jobs as jobs


def setup_due(factory, tenant, actor):
    with factory.begin() as s:
        row = jobs.create_schedule(
            s,
            tenant,
            actor,
            "invitations.cleanup",
            {},
            request_id="create",
            interval_seconds=12,
        )
        jobs.control_schedule(s, tenant, actor, row.id, "resume", 1, "resume")
        row.next_run_at = now() - timedelta(hours=1)
        return row.id


def test_separate_scheduler_worker_and_real_child(scheduled_database):
    engine, factory, tenant, actor = scheduled_database
    with factory.begin() as s:
        target = invitation(s, tenant, actor)
        target_id = target.id
    setup_due(factory, tenant, actor)
    worker = ProcessLoop("worker", tenant_id=tenant)
    assert worker.sweep(engine, max_runs=10, max_seconds=25)["processed"] == 0
    scheduler = ProcessLoop("scheduler", tenant_id=tenant)
    assert scheduler.sweep(engine, max_runs=100, max_seconds=25)["materialized"] == 1
    with factory() as s:
        assert s.get(CompanyInvitation, target_id) is not None
        assert (
            s.scalar(
                select(ScheduledJobRun.status).where(
                    ScheduledJobRun.tenant_id == tenant
                )
            )
            == "pending"
        )
    assert worker.sweep(engine, max_runs=10, max_seconds=25)["succeeded"] == 1
    with factory() as s:
        assert s.get(CompanyInvitation, target_id) is None
        assert (
            s.scalar(
                select(ScheduledJobRun.status).where(
                    ScheduledJobRun.tenant_id == tenant
                )
            )
            == "succeeded"
        )
    assert worker.sweep(engine, max_runs=10, max_seconds=25)["processed"] == 0


def test_concurrent_schedulers_and_claims(scheduled_database):
    _engine, factory, tenant, actor = scheduled_database
    setup_due(factory, tenant, actor)
    barrier = Barrier(2)

    def materialize():
        with factory.begin() as s:
            barrier.wait(timeout=5)
            return jobs.materialize_due(s, tenant)

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: materialize(), range(2)))
    assert sum(results) == 1
    barrier = Barrier(2)

    def claim():
        with factory.begin() as s:
            barrier.wait(timeout=5)
            run = jobs.claim_next(s, tenant)
            return run.id if run else None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: claim(), range(2)))
    assert sum(result is not None for result in results) == 1
    with factory() as s:
        assert (
            s.scalar(
                select(func.count())
                .select_from(ScheduledJobRun)
                .where(ScheduledJobRun.tenant_id == tenant)
            )
            == 1
        )


def test_stopped_worker_does_not_expand_queue_and_cap_preserves_due(
    scheduled_database, monkeypatch
):
    engine, factory, tenant, actor = scheduled_database
    setup_due(factory, tenant, actor)
    monkeypatch.setattr(jobs, "QUEUE_LIMIT", 1)
    with factory.begin() as s:
        jobs.create_manual_run(
            s, tenant, actor, "invitations.cleanup", {}, request_id="fills-cap"
        )
    scheduler = ProcessLoop("scheduler", tenant_id=tenant)
    assert scheduler.sweep(engine, max_runs=100, max_seconds=25)["deferred"] == 1
    with factory.begin() as s:
        run = jobs.claim_next(s, tenant)
        jobs.execute_claim(s, tenant, run.id, run.claim_token)
    assert scheduler.sweep(engine, max_runs=100, max_seconds=25)["materialized"] == 1
    assert scheduler.sweep(engine, max_runs=100, max_seconds=25)["materialized"] == 0


def test_scheduler_reports_revoked_actor_failure(scheduled_database):
    from reality.db.core import TenantMembership

    engine, factory, tenant, actor = scheduled_database
    setup_due(factory, tenant, actor)
    with factory.begin() as s:
        membership = s.scalar(
            select(TenantMembership).where(
                TenantMembership.tenant_id == tenant,
                TenantMembership.user_id == actor,
            )
        )
        membership.status = "removed"
    counts = ProcessLoop("scheduler", tenant_id=tenant).sweep(
        engine, max_runs=1, max_seconds=25
    )
    assert counts["failed"] == 1
    assert counts["materialized"] == 0
    assert counts["budget_exhausted"]


def test_cursor_survives_partial_final_catalog_page(scheduled_database, monkeypatch):
    engine, _factory, _tenant, _actor = scheduled_database
    visited = []
    monkeypatch.setattr(
        jobs,
        "tenant_catalog",
        lambda s, after: [t for t in ["a", "b", "c"] if t > after],
    )
    monkeypatch.setattr(
        jobs, "materialize_due", lambda s, tenant, **kwargs: visited.append(tenant) or 1
    )
    process = ProcessLoop("scheduler")
    for _ in range(3):
        process.sweep(engine, max_runs=1, max_seconds=25)
    assert visited == ["a", "b", "c"]


def test_killed_child_recovers_without_effect(scheduled_database, monkeypatch):
    import subprocess
    import sys
    from time import monotonic

    from reality.jobs import runner

    engine, factory, tenant, actor = scheduled_database
    with factory.begin() as s:
        run = jobs.create_manual_run(
            s, tenant, actor, "invitations.cleanup", {}, request_id="kill"
        )
        jobs.claim_next(s, tenant)
        run_id, token = run.id, run.claim_token
    popen = subprocess.Popen
    children = []

    def stuck_child(*args, **kwargs):
        child = popen(
            [
                sys.executable,
                "-c",
                "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)",
            ],
            **kwargs,
        )
        children.append(child)
        return child

    monkeypatch.setattr(runner.subprocess, "Popen", stuck_child)
    started = monotonic()
    assert runner.execute_process(engine, tenant, run_id, token, timeout=0.3) == "retry"
    assert monotonic() - started < 6
    assert children[0].poll() is not None
    with factory() as s:
        run = s.get(ScheduledJobRun, run_id)
        assert run.last_error_code == "handler_timeout"
        assert run.attempt_count == 1 and run.claim_token is None


def test_cli_manual_replay_status_and_graceful_continuous_stop(
    scheduled_database, tmp_path
):
    import json
    import subprocess
    import sys
    import time

    _engine, _factory, tenant, actor = scheduled_database

    def command(*args):
        result = subprocess.run(
            [sys.executable, "-m", "reality.worker.cli", *args],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return json.loads(result.stdout)

    args = (
        "jobs",
        "run",
        "invitations.cleanup",
        "--tenant",
        tenant,
        "--actor",
        actor,
        "--request-id",
        "cli-manual",
        "--json",
    )
    first = command(*args)
    assert first["status"] == "pending"
    assert command(*args)["id"] == first["id"]
    assert command("once", "--tenant", tenant, "--json")["succeeded"] == 1
    shown = command(
        "runs", "show", first["id"], "--tenant", tenant, "--actor", actor, "--json"
    )
    assert shown["status"] == "succeeded" and "configuration" not in shown
    for role in ("scheduler", "worker"):
        log_path = tmp_path / f"{role}.log"
        with log_path.open("w") as log:
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    f"reality.{role}.cli",
                    "work",
                    "--tenant",
                    tenant,
                ],
                stdout=log,
                stderr=log,
            )
            try:
                deadline = time.monotonic() + 10
                while (
                    f"{role}_sweep" not in log_path.read_text()
                    and time.monotonic() < deadline
                ):
                    assert child.poll() is None
                    time.sleep(0.05)
                assert f"{role}_sweep" in log_path.read_text()
                child.terminate()
                assert child.wait(timeout=5) == 0
            finally:
                if child.poll() is None:
                    child.kill()
                    child.wait(timeout=5)


def test_ten_intervals_with_competing_workers_commit_ten_effects(
    scheduled_database, monkeypatch
):
    from reality.db.core import SecurityAuditEvent, uid
    from reality.jobs import registry

    _engine, factory, tenant, actor = scheduled_database
    schedule_id = setup_due(factory, tenant, actor)
    definition = registry.definitions()["invitations.cleanup"]

    def observed_effect(s, context, config):
        s.add(
            SecurityAuditEvent(
                id=uid("audit"),
                tenant_id=context.tenant_id,
                event_type="scheduled_effect",
            )
        )
        return registry.JobResult(counts={"effects": 1})

    monkeypatch.setitem(
        registry._REGISTRY,
        definition.name,
        registry.JobDefinition(
            definition.name,
            1,
            definition.config_model,
            definition.authorize,
            observed_effect,
        ),
    )
    # Keep the controlled clock beyond freshly generated database defaults.
    clock = now() + timedelta(seconds=1)
    run_ids = set()
    for _ in range(10):
        monkeypatch.setattr(jobs, "now", lambda at=clock: at)
        with factory.begin() as s:
            assert jobs.materialize_due(s, tenant) == 1
        barrier = Barrier(2)

        def attempt(start=barrier):
            with factory.begin() as s:
                start.wait(timeout=5)
                claim = jobs.claim_next(s, tenant)
                if claim is None:
                    return None
                run_id, token = claim.id, claim.claim_token
            with factory.begin() as s:
                assert jobs.execute_claim(s, tenant, run_id, token) == "succeeded"
            return run_id

        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(lambda _: attempt(), range(2)))
        assert sum(value is not None for value in outcomes) == 1
        run_ids.update(value for value in outcomes if value)
        with factory() as s:
            clock = jobs._schedule(s, tenant, schedule_id).next_run_at
    assert len(run_ids) == 10
    with factory() as s:
        assert (
            s.scalar(
                select(func.count())
                .select_from(SecurityAuditEvent)
                .where(
                    SecurityAuditEvent.tenant_id == tenant,
                    SecurityAuditEvent.event_type == "scheduled_effect",
                )
            )
            == 10
        )
