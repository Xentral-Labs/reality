import json

import pytest
from sqlalchemy import event, select

from reality.db.core import SourceRecord
from reality.services import core


def test_bound_enqueue_does_not_commit_and_rolls_back(session, business):
    def deny_commit(_session):
        pytest.fail("Caller-owned intake committed")

    event.listen(session, "before_commit", deny_commit)
    try:
        with pytest.raises(RuntimeError), session.begin_nested():
            core.enqueue_source(
                session,
                business.tenant.id,
                "demo_data",
                "order",
                "rollback",
                {"number": "DEMO-1"},
                _commit=False,
            )
            raise RuntimeError("rollback proof")
    finally:
        event.remove(session, "before_commit", deny_commit)
    assert (
        session.scalar(
            select(SourceRecord.id).where(
                SourceRecord.tenant_id == business.tenant.id,
                SourceRecord.external_id == "rollback",
            )
        )
        is None
    )


def test_bound_interpretation_failure_retains_intake_without_committing(
    session, business
):
    from reality.db.core import Document, ImportJob, InterpretationOutcome

    source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "demo_data",
        "order",
        "bad-order",
        {"number": "Invalid"},
        _commit=False,
    )

    def deny_root_commit(db):
        if not db.in_nested_transaction():
            pytest.fail("Bound interpretation committed the caller transaction")

    event.listen(session, "before_commit", deny_root_commit)
    try:
        assert (
            core.process_import_job_bound(session, business.tenant.id, job.id) is None
        )
    finally:
        event.remove(session, "before_commit", deny_root_commit)
    assert session.get(ImportJob, job.id).status == "failed"
    assert (
        session.scalar(
            select(Document.id).where(
                Document.tenant_id == business.tenant.id,
                Document.source_record_id == source.id,
            )
        )
        is None
    )
    assert (
        session.scalar(
            select(InterpretationOutcome.classification).where(
                InterpretationOutcome.tenant_id == business.tenant.id,
                InterpretationOutcome.import_job_id == job.id,
            )
        )
        == "failed"
    )
    session.rollback()


@pytest.mark.parametrize("pending", [False, True])
@pytest.mark.parametrize("content", ["empty", "international_demo"])
def test_ten_worker_occurrences_create_orders_without_business_execution(
    session, scheduled_owner, monkeypatch, pending, content
):
    from datetime import timedelta

    from sqlalchemy import func

    from reality.db.core import Commitment, Document, Movement, Reservation, now
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.services import company_setup, demo_data, scheduled_jobs

    monkeypatch.setattr("reality.integrations.demo_data.burst_size", lambda *args: 1)
    if pending:
        scheduled_owner.status = "pending_approval"
        session.commit()
    actor = scheduled_owner.id
    setup = company_setup.create_company(
        session,
        actor,
        "worker-empty",
        "Live Sandbox",
        "sandbox",
        content,
        confirmed=True,
    )
    tenant = setup["tenant_id"]
    baseline_counts = {
        model: session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in (Document, Commitment, Movement, Reservation)
    }
    import json

    from reality.db.core import PlaygroundRun

    manifest_before = json.dumps(
        session.get(PlaygroundRun, setup["run_id"]).initialization_progress,
        sort_keys=True,
    )
    preview = demo_data.preview(session, tenant, actor)
    connected = demo_data.connect(
        session, tenant, actor, "worker-connect", preview["fingerprint"], confirmed=True
    )
    started = demo_data.control(
        session,
        tenant,
        actor,
        "start",
        connected["revision"],
        "worker-start",
        confirmed=True,
        rate=300,
    )
    schedule = session.get(ScheduledJob, started["schedule_id"])
    for index in range(10):
        schedule.next_run_at = now() - timedelta(seconds=11 - index)
        session.commit()
        scheduled_jobs.materialize_due(session, tenant)
        session.commit()
        claim = scheduled_jobs.claim_next(session, tenant)
        assert claim is not None
        token, run_id = claim.claim_token, claim.id
        session.commit()
        assert (
            scheduled_jobs.execute_claim(session, tenant, run_id, token) == "succeeded"
        )
        session.commit()
        assert (
            scheduled_jobs.execute_claim(session, tenant, run_id, token) == "succeeded"
        )
    result = demo_data.status(session, tenant, actor)
    assert result["generated"] == result["imported"] == 10 and result["failed"] == 0
    for model, count in (
        (Document, 10),
        (Commitment, 10),
        (Movement, 0),
        (Reservation, 0),
    ):
        assert (
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tenant)
            )
            == count + baseline_counts[model]
        )

    assert (
        json.dumps(
            session.get(PlaygroundRun, setup["run_id"]).initialization_progress,
            sort_keys=True,
        )
        == manifest_before
    )

    from reality.db.core import ImportJob

    jobs = list(session.scalars(select(ImportJob).where(ImportJob.tenant_id == tenant)))
    stamp = now()
    for job in jobs:
        job.created_at = stamp
    max(jobs, key=lambda row: row.id).created_at = stamp - timedelta(days=1)
    session.flush()
    expected = sorted(jobs, key=lambda row: (row.created_at, row.id), reverse=True)
    recent = demo_data.imports(session, tenant, actor, limit=2, recent=True)
    assert [row["id"] for row in recent["items"]] == [row.id for row in expected[:2]]
    assert recent["has_more"] and recent["next_cursor"] is None
    assert all(
        row["created_at"] and row["completed_at"] and row["document_number"]
        for row in recent["items"]
    )
    with pytest.raises(core.InvalidOperation):
        demo_data.imports(session, tenant, actor, recent=True, cursor="invalid")

    first_page = demo_data.imports(session, tenant, actor, limit=2)
    second_page = demo_data.imports(
        session, tenant, actor, limit=2, cursor=first_page["next_cursor"]
    )
    assert {row["id"] for row in first_page["items"]}.isdisjoint(
        row["id"] for row in second_page["items"]
    )
    detail = demo_data.read_import(session, tenant, actor, first_page["items"][0]["id"])
    assert detail["document_id"] and detail["payload"]["synthetic"] is True
    assert detail["outcomes"][0]["classification"] == "interpreted"
    if not pending and content == "empty":
        other = company_setup.create_company(
            session,
            actor,
            "cursor-other",
            "Other Sandbox",
            "sandbox",
            "empty",
            confirmed=True,
        )["tenant_id"]
        demo_data.connect(
            session,
            other,
            actor,
            "cursor-connect",
            demo_data.preview(session, other, actor)["fingerprint"],
            confirmed=True,
        )
        with pytest.raises(core.InvalidOperation):
            demo_data.imports(session, other, actor, cursor=first_page["next_cursor"])


def test_twenty_failed_imports_pause_and_retry_same_sources(
    session, scheduled_owner, monkeypatch
):
    from datetime import timedelta

    from reality.db.core import ImportJob, now
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.services import company_setup, demo_data, scheduled_jobs

    monkeypatch.setattr("reality.integrations.demo_data.burst_size", lambda *args: 1)
    actor = scheduled_owner.id
    setup = company_setup.create_company(
        session, actor, "pressure-empty", "Pressure", "sandbox", "empty", confirmed=True
    )
    tenant = setup["tenant_id"]
    connected = demo_data.connect(
        session,
        tenant,
        actor,
        "pressure-connect",
        demo_data.preview(session, tenant, actor)["fingerprint"],
        confirmed=True,
    )
    started = demo_data.control(
        session,
        tenant,
        actor,
        "start",
        connected["revision"],
        "pressure-start",
        confirmed=True,
    )
    schedule = session.get(ScheduledJob, started["schedule_id"])
    interpreter = core.SOURCE_INTERPRETERS[("demo_data", "order")]

    def unavailable(*args):
        raise core.InvalidOperation("Synthetic validation failure")

    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("demo_data", "order"), unavailable)
    for index in range(20):
        schedule.next_run_at = now() - timedelta(seconds=21 - index)
        session.commit()
        scheduled_jobs.materialize_due(session, tenant)
        claim = scheduled_jobs.claim_next(session, tenant)
        session.commit()
        scheduled_jobs.execute_claim(session, tenant, claim.id, claim.claim_token)
        session.commit()
    paused = demo_data.status(session, tenant, actor)
    assert paused["state"] == "paused" and paused["failed"] == 20
    assert paused["next_arrival"] is None
    # Feature 168 FR-020: saturation pauses the settlement stream as well.
    assert paused["order_to_cash"]["next_settlement"] is None
    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("demo_data", "order"), interpreter)
    job = session.scalar(
        select(ImportJob).where(
            ImportJob.tenant_id == tenant, ImportJob.status == "failed"
        )
    )
    source_id = job.source_record_id
    assert (
        demo_data.retry_import(session, tenant, actor, job.id, confirmed=True)["status"]
        == "completed"
    )
    assert job.source_record_id == source_id
    assert demo_data.status(session, tenant, actor)["generated"] == 20


def test_unexpected_interpreter_failure_rolls_back_source_and_retries_same_delivery(
    session, scheduled_owner, monkeypatch
):
    from datetime import timedelta

    from reality.db.core import now
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.services import company_setup, demo_data, scheduled_jobs

    monkeypatch.setattr("reality.integrations.demo_data.burst_size", lambda *args: 1)
    actor = scheduled_owner.id
    tenant = company_setup.create_company(
        session, actor, "atomic-worker", "Atomic", "sandbox", "empty", confirmed=True
    )["tenant_id"]
    connected = demo_data.connect(
        session,
        tenant,
        actor,
        "atomic-connect",
        demo_data.preview(session, tenant, actor)["fingerprint"],
        confirmed=True,
    )
    started = demo_data.control(
        session,
        tenant,
        actor,
        "start",
        connected["revision"],
        "atomic-start",
        confirmed=True,
    )
    schedule = session.get(ScheduledJob, started["schedule_id"])
    schedule.next_run_at = now() - timedelta(seconds=1)
    session.commit()
    scheduled_jobs.materialize_due(session, tenant)
    claim = scheduled_jobs.claim_next(session, tenant)
    run_id, token = claim.id, claim.claim_token
    session.commit()
    interpreter = core.SOURCE_INTERPRETERS[("demo_data", "order")]

    def failure(*args):
        raise RuntimeError("unexpected failure after intake")

    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("demo_data", "order"), failure)
    with pytest.raises(RuntimeError), session.begin_nested():
        scheduled_jobs.execute_claim(session, tenant, run_id, token)
    assert demo_data.status(session, tenant, actor)["generated"] == 0
    scheduled_jobs.record_failure(
        session, tenant, run_id, token, "transient", retryable=True
    )
    claim.next_attempt_at = now() - timedelta(seconds=1)
    session.commit()
    monkeypatch.setitem(core.SOURCE_INTERPRETERS, ("demo_data", "order"), interpreter)
    retried = scheduled_jobs.claim_next(session, tenant)
    assert retried.id == run_id
    scheduled_jobs.execute_claim(session, tenant, retried.id, retried.claim_token)
    session.commit()
    assert demo_data.status(session, tenant, actor)["generated"] == 1


def _tick(session, tenant, schedule):
    from datetime import timedelta

    from reality.db.core import now
    from reality.services import scheduled_jobs

    schedule.next_run_at = now() - timedelta(seconds=1)
    session.commit()
    scheduled_jobs.materialize_due(session, tenant)
    session.commit()
    claim = scheduled_jobs.claim_next(session, tenant)
    assert claim is not None
    run_id, token = claim.id, claim.claim_token
    session.commit()
    assert scheduled_jobs.execute_claim(session, tenant, run_id, token) == "succeeded"
    session.commit()
    return run_id, token


def _running_demo(session, monkeypatch, actor, slug):
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.services import company_setup, demo_data

    tenant = company_setup.create_company(
        session, actor, slug, "Varied Sandbox", "sandbox", "empty", confirmed=True
    )["tenant_id"]
    connected = demo_data.connect(
        session,
        tenant,
        actor,
        f"{slug}-connect",
        demo_data.preview(session, tenant, actor)["fingerprint"],
        confirmed=True,
    )
    started = demo_data.control(
        session,
        tenant,
        actor,
        "start",
        connected["revision"],
        f"{slug}-start",
        confirmed=True,
    )
    return tenant, session.get(ScheduledJob, started["schedule_id"])


def test_one_delivery_carries_none_one_or_two_orders_with_stable_identities(
    session, scheduled_owner, monkeypatch
):
    from reality.db.core import Document
    from reality.integrations import demo_data as synthetic
    from reality.services import demo_data, scheduled_jobs

    actor = scheduled_owner.id
    tenant, schedule = _running_demo(session, monkeypatch, actor, "burst")

    monkeypatch.setattr(synthetic, "burst_size", lambda *args: 2)
    run_id, token = _tick(session, tenant, schedule)
    sources = list(
        session.scalars(
            select(SourceRecord)
            .where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_system == "demo_data",
                SourceRecord.source_type == "order",
            )
            .order_by(SourceRecord.external_id)
        )
    )
    assert [row.external_id for row in sources] == [
        f"{schedule.id}:{run_id}",
        f"{schedule.id}:{run_id}:2",
    ]
    numbers = sorted(
        session.scalars(
            select(Document.number).where(
                Document.tenant_id == tenant, Document.type == "sales_order"
            )
        )
    )
    assert len(numbers) == 2 and numbers[1] == f"{numbers[0]}-2"
    assert demo_data.status(session, tenant, actor)["imported"] == 2
    # Replaying the same delivery reuses both stored payloads.
    assert scheduled_jobs.execute_claim(session, tenant, run_id, token) == "succeeded"
    session.commit()
    assert demo_data.status(session, tenant, actor)["generated"] == 2

    monkeypatch.setattr(synthetic, "burst_size", lambda *args: 0)
    _tick(session, tenant, schedule)
    state = demo_data.status(session, tenant, actor)
    assert state["generated"] == 2 and state["state"] == "running"


def test_growing_customer_pool_keeps_the_run_and_start_adds_the_newcomers(
    session, scheduled_owner, monkeypatch
):
    from reality.db.core import Party
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.integrations import demo_data as synthetic
    from reality.services import demo_data

    actor = scheduled_owner.id
    tenant, schedule = _running_demo(session, monkeypatch, actor, "pool")
    newcomer = {"key": "C21", "name": "Harbor Lane Books", "role": "customer"}
    monkeypatch.setattr(
        demo_data,
        "DEMO_DATA_CUSTOMERS",
        demo_data.DEMO_DATA_CUSTOMERS + ((newcomer["key"], newcomer["name"]),),
    )
    assert demo_data.preview(session, tenant, actor)["add"]["parties"] == [newcomer]

    # A run started before the pool grew keeps delivering.
    monkeypatch.setattr(synthetic, "burst_size", lambda *args: 1)
    _tick(session, tenant, schedule)
    state = demo_data.status(session, tenant, actor)
    assert state["imported"] == 1 and state["scheduler_error"] is None

    stopped = demo_data.control(
        session, tenant, actor, "stop", state["revision"], "pool-stop", confirmed=True
    )
    restarted = demo_data.control(
        session,
        tenant,
        actor,
        "start",
        stopped["revision"],
        "pool-restart",
        confirmed=True,
    )
    party = session.scalar(
        select(Party).where(Party.tenant_id == tenant, Party.name == newcomer["name"])
    )
    assert party is not None
    references = session.get(ScheduledJob, restarted["schedule_id"]).configuration[
        "arguments"
    ]["references"]
    assert references["parties"]["C21"] == party.id
    assert demo_data.preview(session, tenant, actor)["add"]["parties"] == []


@pytest.mark.parametrize("kind", ["invoice", "payment"])
def test_bound_processing_accepts_all_synthetic_types(session, business, kind):
    """Feature 168 FR-017: invoices and payments share the order's savepoint path."""
    from reality.db.core import ImportJob, InterpretationOutcome

    _source, job = core.enqueue_source(
        session,
        business.tenant.id,
        "demo_data",
        kind,
        f"bad-{kind}",
        {"schema_version": 1, "synthetic": True, "broken": True},
        _commit=False,
    )
    assert core.process_import_job_bound(session, business.tenant.id, job.id) is None
    assert session.get(ImportJob, job.id).status == "failed"
    outcome = session.scalar(
        select(InterpretationOutcome).where(
            InterpretationOutcome.tenant_id == business.tenant.id,
            InterpretationOutcome.import_job_id == job.id,
        )
    )
    assert outcome.classification == "failed"
    assert outcome.interpreter_name == f"demo_data.{kind}"
    assert kind in outcome.summary
    _foreign, foreign_job = core.enqueue_source(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "not-synthetic",
        {"id": 1},
        _commit=False,
    )
    with pytest.raises(core.InvalidOperation, match="registered Demo Data source"):
        core.process_import_job_bound(session, business.tenant.id, foreign_job.id)
    session.rollback()


def _settle_all(session, tenant, settlement, *, max_ticks=8):
    """Tick the settlement schedule until it emits nothing more; return per-tick counts."""
    from sqlalchemy import func

    from reality.db.core import SourceRecord

    def counts():
        return {
            kind: session.scalar(
                select(func.count())
                .select_from(SourceRecord)
                .where(
                    SourceRecord.tenant_id == tenant,
                    SourceRecord.source_system == "demo_data",
                    SourceRecord.source_type == kind,
                )
            )
            for kind in ("invoice", "payment")
        }

    history, before = [], counts()
    for _ in range(max_ticks):
        _tick(session, tenant, settlement)
        session.refresh(settlement)
        after = counts()
        history.append({kind: after[kind] - before[kind] for kind in after})
        if after == before:
            break
        before = after
    return history, before


def test_settlement_occurrence_emits_due_records_in_bounded_batches(
    session, scheduled_owner, monkeypatch
):
    """Feature 168 FR-018: due invoices and payments, oldest first, at most ten per occurrence."""
    from datetime import timedelta

    from sqlalchemy import func

    from reality.db.core import Document, Movement, Reservation, SourceRecord, now
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.integrations import demo_data as synthetic
    from reality.services import demo_data

    monkeypatch.setattr("reality.integrations.demo_data.burst_size", lambda *args: 1)
    # The production bound leaves headroom at 300 orders per hour; the test uses a
    # batch of ten so a dozen orders exercise the bound in two occurrences.
    assert demo_data.SETTLEMENT_BATCH == 25
    monkeypatch.setattr(demo_data, "SETTLEMENT_BATCH", 10)
    # Compressed delays collapse to zero so every non-late story is due at once.
    monkeypatch.setattr(
        synthetic,
        "DELAYS",
        {k: (0, 0) for k in ("invoice", "provider", "bank", "second")},
    )
    actor = scheduled_owner.id
    tenant, order_schedule = _running_demo(session, monkeypatch, actor, "settle")
    for _ in range(12):
        _tick(session, tenant, order_schedule)
        session.refresh(order_schedule)
    orders = list(
        session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant, SourceRecord.source_type == "order"
            )
        )
    )
    assert len(orders) == 12
    # One order is older than the scan window: it is left alone until it returns.
    stale = orders[0]
    stale.received_at = now() - timedelta(days=40)
    session.flush()
    seed = order_schedule.configuration["arguments"]["seed"]
    plans = {
        order.external_id: synthetic.settlement_plan(
            seed, order_schedule.id, order.external_id, json.loads(order.payload)
        )
        for order in orders
    }
    expected_payments = sum(
        len(plan.payments)
        for external_id, plan in plans.items()
        if plan.outcome != "late" and external_id != stale.external_id
    )
    movements_before = session.scalar(
        select(func.count()).select_from(Movement).where(Movement.tenant_id == tenant)
    )
    status = demo_data.status(session, tenant, actor)
    settlement = session.get(ScheduledJob, status["settlement_schedule_id"])

    history, totals = _settle_all(session, tenant, settlement)
    assert all(sum(tick.values()) <= 10 for tick in history)
    assert history[0] == {"invoice": 10, "payment": 0}
    assert totals == {"invoice": 11, "payment": expected_payments}
    # Every payment follows its own invoice, never precedes it.
    for order in orders:
        if order is stale:
            continue
        invoice = session.scalar(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.external_id == f"{order.external_id}:invoice",
            )
        )
        payments = list(
            session.scalars(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant,
                    SourceRecord.source_type == "payment",
                    SourceRecord.external_id.like(f"{order.external_id}:payment:%"),
                )
            )
        )
        assert invoice is not None
        assert all(payment.received_at >= invoice.received_at for payment in payments)
        plan = plans[order.external_id]
        if plan.outcome == "late":
            assert payments == []
        else:
            assert len(payments) == len(plan.payments)
    # Money moved through the ledger; nothing else executed.
    assert (
        session.scalar(
            select(func.count())
            .select_from(Movement)
            .where(Movement.tenant_id == tenant)
        )
        == movements_before
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(Reservation)
            .where(Reservation.tenant_id == tenant)
        )
        == 0
    )
    exact = [
        oid
        for oid, plan in plans.items()
        if plan.outcome == "exact" and oid != stale.external_id
    ]
    for external_id in exact:
        invoice_document = session.scalar(
            select(Document)
            .join(SourceRecord, SourceRecord.id == Document.source_record_id)
            .where(
                Document.tenant_id == tenant,
                SourceRecord.external_id == f"{external_id}:invoice",
            )
        )
        assert core.open_invoice_amount(session, tenant, invoice_document.id) == 0
    block = demo_data.status(session, tenant, actor)["order_to_cash"]
    assert block["invoices_issued"] == 11
    assert block["payments_received"] == expected_payments
    assert block["invoices_settled"] >= len(exact)
    assert block["last_settlement"] is not None

    # Idle occurrences emit nothing; the stale order returns to the scan once it
    # is back inside the window.
    assert demo_data.settlement_work(session, tenant, now()) == []
    stale.received_at = now()
    session.flush()
    work = demo_data.settlement_work(session, tenant, now())
    assert [item["source_type"] for item in work] == ["invoice"]
    assert work[0]["external_id"] == f"{stale.external_id}:invoice"


def test_settlement_uses_each_order_schedule_seed_and_pause_never_bursts(
    session, scheduled_owner, monkeypatch
):
    """Feature 168 FR-018/FR-019: old orders keep their seed; resume drains ten at a time."""
    from reality.db.core import SourceRecord
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.integrations import demo_data as synthetic
    from reality.services import demo_data

    monkeypatch.setattr("reality.integrations.demo_data.burst_size", lambda *args: 1)
    monkeypatch.setattr(demo_data, "SETTLEMENT_BATCH", 10)
    monkeypatch.setattr(
        synthetic,
        "DELAYS",
        {k: (0, 0) for k in ("invoice", "provider", "bank", "second")},
    )
    actor = scheduled_owner.id
    tenant, first_schedule = _running_demo(session, monkeypatch, actor, "seeds")
    for _ in range(3):
        _tick(session, tenant, first_schedule)
        session.refresh(first_schedule)
    status = demo_data.status(session, tenant, actor)
    stopped = demo_data.control(
        session, tenant, actor, "stop", status["revision"], "stop", confirmed=True
    )
    restarted = demo_data.control(
        session, tenant, actor, "start", stopped["revision"], "again", confirmed=True
    )
    second_schedule = session.get(ScheduledJob, restarted["schedule_id"])
    for _ in range(2):
        _tick(session, tenant, second_schedule)
        session.refresh(second_schedule)
    settlement = session.get(ScheduledJob, restarted["settlement_schedule_id"])
    _settle_all(session, tenant, settlement)
    for schedule in (first_schedule, second_schedule):
        seed = schedule.configuration["arguments"]["seed"]
        for order in session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == tenant,
                SourceRecord.source_type == "order",
                SourceRecord.external_id.like(f"{schedule.id}:%"),
            )
        ):
            plan = synthetic.settlement_plan(
                seed, schedule.id, order.external_id, json.loads(order.payload)
            )
            invoice = session.scalar(
                select(SourceRecord).where(
                    SourceRecord.tenant_id == tenant,
                    SourceRecord.external_id == f"{order.external_id}:invoice",
                )
            )
            assert json.loads(invoice.payload)["number"] == plan.invoice_number
    # Thirteen more orders arrive, then the owner pauses for a long time. Resume
    # never bursts: the backlog drains ten records per occurrence.
    for _ in range(13):
        _tick(session, tenant, second_schedule)
        session.refresh(second_schedule)
    current = demo_data.status(session, tenant, actor)
    paused = demo_data.control(
        session, tenant, actor, "pause", current["revision"], "pause", confirmed=True
    )
    resumed = demo_data.control(
        session, tenant, actor, "resume", paused["revision"], "resume", confirmed=True
    )
    settlement = session.get(ScheduledJob, resumed["settlement_schedule_id"])
    history, _ = _settle_all(session, tenant, settlement)
    assert history[0] == {"invoice": 10, "payment": 0}
    assert all(sum(tick.values()) <= 10 for tick in history)
