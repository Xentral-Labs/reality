"""Staged cost generations through the existing shared queue and claim boundary."""

from decimal import Decimal

import pytest
from sqlalchemy import text

from benchmarks.large_tenant_registers.costing_dataset import Profile, build
from benchmarks.large_tenant_registers.costing_generations import (
    initialize,
    snapshot,
    start_generation,
    work_generation,
)
from benchmarks.large_tenant_registers.costing_worker import (
    initialize_queue,
    registered,
)
from reality.db.core import now
from reality.jobs.registry import JobError
from reality.services import scheduled_jobs as jobs


def prepare(connection):
    build(connection, Profile.named("reduced"))
    initialize(connection)
    initialize_queue(connection)


def finish(connection, tenant, generation):
    while not work_generation(connection, tenant, generation, max_ranges=1)[
        "published"
    ]:
        pass


def test_staged_rows_are_hidden_and_late_evidence_keeps_frozen_revision(session):
    c = session.connection()
    prepare(c)
    generation = start_generation(c, "a", movement_budget=100)
    assert start_generation(c, "a", movement_budget=100) == generation
    first = work_generation(c, "a", generation, max_ranges=1)
    assert not first["published"]
    assert snapshot(c, "a", 1)["state"] == "not_ready"
    c.execute(
        text("INSERT INTO costing_spike.adjustment VALUES ('a',1,1,10,'source:late:1')")
    )
    finish(c, "a", generation)
    old = snapshot(c, "a", 1)
    assert old["state"] == "pending" and old["published_revision"] == 0
    next_generation = start_generation(c, "a", movement_budget=100)
    work_generation(c, "a", next_generation, max_ranges=1)
    assert snapshot(c, "a", 1) == old
    finish(c, "a", next_generation)
    current = snapshot(c, "a", 1)
    assert (
        current["state"] == "ready" and current["value"]["cost"] != old["value"]["cost"]
    )
    assert c.scalar(
        text("SELECT amount FROM costing_spike.component WHERE tenant='a' AND id=1")
    ) == Decimal(41)
    assert work_generation(c, "a", next_generation)["ranges"] == 0


def test_oversized_pool_and_foreign_generation_refused(session):
    c = session.connection()
    prepare(c)
    with pytest.raises(ValueError, match="pool"):
        start_generation(c, "a", movement_budget=1)
    generation = start_generation(c, "a", movement_budget=100)
    with pytest.raises(ValueError, match="not found"):
        work_generation(c, "b", generation)
    assert snapshot(c, "b", 1)["state"] == "not_ready"


def test_shared_claim_failure_retry_and_success_replay(session, monkeypatch):
    from benchmarks.large_tenant_registers import costing_worker as worker

    c = session.connection()
    prepare(c)
    generation = start_generation(c, "a", movement_budget=100)
    with registered():
        run = jobs.enqueue_projection_run(session, "a", [f"costing:{generation}"])
        claim = jobs.claim_next(session, "a")
        assert run.id == claim.id
        token = claim.claim_token
        real = worker.work_generation

        def failing(*args, **kwargs):
            real(*args, **kwargs)
            raise RuntimeError("crash before transaction commit")

        with monkeypatch.context() as patch:
            patch.setattr(worker, "work_generation", failing)
            with pytest.raises(RuntimeError), session.begin_nested():
                jobs.execute_claim(session, "a", run.id, token)
        assert (
            c.scalar(
                text(
                    "SELECT cursor FROM costing_spike.generation WHERE tenant='a' AND id=:id"
                ),
                {"id": generation},
            )
            == 0
        )
        assert (
            jobs.record_failure(
                session, "a", run.id, token, "child_exited", retryable=True
            )
            == "retry"
        )
        run.next_attempt_at = now()
        session.flush()
        claim = jobs.claim_next(session, "a")
        with pytest.raises(JobError, match="stale_claim"), session.begin_nested():
            jobs.execute_claim(session, "a", run.id, token)
        assert (
            jobs.execute_claim(session, "a", run.id, claim.claim_token) == "succeeded"
        )
        cursor = c.scalar(
            text(
                "SELECT cursor FROM costing_spike.generation WHERE tenant='a' AND id=:id"
            ),
            {"id": generation},
        )
        assert jobs.execute_claim(session, "a", run.id, "lost-response") == "succeeded"
        assert (
            c.scalar(
                text(
                    "SELECT cursor FROM costing_spike.generation WHERE tenant='a' AND id=:id"
                ),
                {"id": generation},
            )
            == cursor
        )


def test_archived_tenant_cannot_claim_staged_work(session):
    c = session.connection()
    prepare(c)
    generation = start_generation(c, "a", movement_budget=100)
    with registered():
        jobs.enqueue_projection_run(session, "a", [f"costing:{generation}"])
        c.execute(
            text("UPDATE public.tenant SET archived_at=clock_timestamp() WHERE id='a'")
        )
        assert jobs.claim_next(session, "a") is None
        assert (
            c.scalar(
                text(
                    "SELECT cursor FROM costing_spike.generation WHERE tenant='a' AND id=:id"
                ),
                {"id": generation},
            )
            == 0
        )


def test_canonical_report_relation_preserves_coverage_and_generation(session):
    from datetime import date

    from benchmarks.large_tenant_registers.costing_cases import (
        derive,
        monthly_read,
        publish,
    )
    from benchmarks.large_tenant_registers.costing_generations import report_month

    c = session.connection()
    prepare(c)
    generation = start_generation(c, "a", movement_budget=100)
    finish(c, "a", generation)
    rows, inventory = derive(c, "a")
    publish(c, "a", rows, inventory)
    actual = report_month(c, "a", date(2026, 9, 1))
    expected = monthly_read(c, "a", date(2026, 9, 1))
    assert [
        {key: row[key] for key in ("item", "revenue", "db1", "db2")} for row in actual
    ] == expected
    assert report_month(c, "foreign", date(2026, 9, 1)) == []


def test_normal_registry_does_not_accept_experimental_generation():
    from reality.jobs.registry import get_definition

    with pytest.raises(JobError):
        get_definition("projections.refresh").validate(
            {"names": ["costing:" + "0" * 32]}
        )


@pytest.fixture
def committed_costing_database(monkeypatch):
    """Disposable named database admitted by the guarded experimental child."""
    import os
    from pathlib import Path
    from uuid import uuid4

    from sqlalchemy import create_engine
    from sqlalchemy.engine import make_url

    name = "reality_benchmark_costing_" + uuid4().hex
    admin = create_engine(
        make_url(os.environ["REALITY_DATABASE_URL"]).set(database="postgres"),
        isolation_level="AUTOCOMMIT",
    )
    with admin.connect() as c:
        c.execute(text(f'CREATE DATABASE "{name}"'))
    url = admin.url.set(database=name).render_as_string(hide_password=False)
    engine = create_engine(url)
    monkeypatch.setenv("REALITY_DATABASE_URL", url)
    core = Path(__file__).resolve().parents[1]
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join([str(core / "src"), str(core)]))
    try:
        with engine.begin() as c:
            prepare(c)
        yield engine
    finally:
        engine.dispose()
        with admin.connect() as c:
            c.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()


def test_actual_child_timeout_retries_without_partial_publication(
    committed_costing_database,
):
    from sqlalchemy.orm import Session

    from benchmarks.large_tenant_registers.costing_worker import execute_process

    engine = committed_costing_database
    with engine.begin() as c:
        generation = start_generation(c, "a")
    with registered():
        with Session(engine) as session, session.begin():
            jobs.enqueue_projection_run(session, "a", [f"costing:{generation}"])
            run = jobs.claim_next(session, "a")
            identity, token = run.id, run.claim_token
        assert execute_process(engine, "a", identity, token, timeout=0.001) == "retry"
        with engine.begin() as c:
            assert snapshot(c, "a", 1)["state"] == "not_ready"
            assert c.scalar(text("SELECT cursor FROM costing_spike.generation")) == 0
            c.execute(
                text(
                    "UPDATE public.scheduled_job_run SET next_attempt_at=clock_timestamp() WHERE id=:id"
                ),
                {"id": identity},
            )
        with Session(engine) as session, session.begin():
            run = jobs.claim_next(session, "a")
            assert run.id == identity and run.claim_token != token
            token = run.claim_token
        # This test proves retry atomicity, not the separately qualified 30-second
        # reference-host budget; allow slower local and CI machines to finish.
        assert execute_process(engine, "a", identity, token, timeout=120) == "succeeded"
    with engine.connect() as c:
        assert snapshot(c, "a", 1)["state"] == "ready"


def test_reader_keeps_one_generation_across_atomic_publication(
    committed_costing_database,
):
    engine = committed_costing_database
    with engine.begin() as c:
        finish(c, "a", start_generation(c, "a"))
        c.execute(
            text(
                "INSERT INTO costing_spike.adjustment VALUES ('a',1,1,10,'source:late:1')"
            )
        )
        generation = start_generation(c, "a", movement_budget=100)
        work_generation(c, "a", generation, max_ranges=1)
    with engine.connect().execution_options(
        isolation_level="REPEATABLE READ"
    ) as reader:
        before = snapshot(reader, "a", 1)
        assert before["state"] == "pending"
        with engine.begin() as writer:
            finish(writer, "a", generation)
        assert snapshot(reader, "a", 1) == before
    with engine.connect() as reader:
        after = snapshot(reader, "a", 1)
        assert after["state"] == "ready"
        assert after["generation"] != before["generation"]
        assert after["value"]["cost"] != before["value"]["cost"]
