import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import Item, Movement
from reality.demo.international import DEMO_DATA_CUSTOMERS
from reality.services import company_setup
from reality.services.core import Conflict


def test_connect_stopped_prerequisites_and_explicit_lifecycle(
    session, scheduled_owner, monkeypatch
):
    from reality.services import demo_data

    result = company_setup.create_company(
        session,
        scheduled_owner.id,
        "live-empty",
        "Live Practice",
        "sandbox",
        "empty",
        confirmed=True,
    )
    tenant, actor = result["tenant_id"], scheduled_owner.id
    preview = demo_data.preview(session, tenant, actor)
    assert len(preview["add"]["items"]) == 4
    assert [row["key"] for row in preview["add"]["parties"]] == [
        "company",
        *(key for key, _ in DEMO_DATA_CUSTOMERS),
    ]
    assert (
        session.scalar(
            select(func.count()).select_from(Item).where(Item.tenant_id == tenant)
        )
        == 0
    )
    connection = demo_data.connect(
        session, tenant, actor, "connect", preview["fingerprint"], confirmed=True
    )
    assert connection["state"] == "stopped" and connection["next_arrival"] is None
    assert (
        session.scalar(
            select(func.count())
            .select_from(Movement)
            .where(Movement.tenant_id == tenant)
        )
        == 0
    )
    running = demo_data.control(
        session, tenant, actor, "start", connection["revision"], "start", confirmed=True
    )
    assert running["state"] == "running" and running["rate"] == 60
    assert (
        demo_data.control(
            session,
            tenant,
            actor,
            "start",
            connection["revision"],
            "start",
            confirmed=True,
        )["schedule_id"]
        == running["schedule_id"]
    )
    with pytest.raises(Conflict):
        demo_data.control(
            session,
            tenant,
            actor,
            "pause",
            connection["revision"],
            "stale",
            confirmed=True,
        )
    paused = demo_data.control(
        session, tenant, actor, "pause", running["revision"], "pause", confirmed=True
    )
    resumed = demo_data.control(
        session, tenant, actor, "resume", paused["revision"], "resume", confirmed=True
    )
    assert resumed["schedule_id"] == running["schedule_id"]
    stopped = demo_data.control(
        session, tenant, actor, "stop", resumed["revision"], "stop", confirmed=True
    )
    restarted = demo_data.control(
        session,
        tenant,
        actor,
        "start",
        stopped["revision"],
        "start-new",
        confirmed=True,
    )
    assert restarted["schedule_id"] != running["schedule_id"]


def test_rates_disconnect_and_reconnect_preserve_source(
    session, scheduled_owner, monkeypatch
):
    from reality.services import demo_data

    actor = scheduled_owner.id
    tenant = company_setup.create_company(
        session, actor, "rates", "Rates", "sandbox", "empty", confirmed=True
    )["tenant_id"]
    preview = demo_data.preview(session, tenant, actor)
    state = demo_data.connect(
        session, tenant, actor, "connect-rates", preview["fingerprint"], confirmed=True
    )
    connection_id = state["id"]
    for index, (action, rate, expected) in enumerate(
        [
            ("set_rate", 10, "stopped"),
            ("start", 10, "running"),
            ("set_rate", 300, "running"),
            ("disconnect", None, "disconnected"),
            ("reconnect", None, "stopped"),
            ("start", 60, "running"),
        ]
    ):
        state = demo_data.control(
            session,
            tenant,
            actor,
            action,
            state["revision"],
            f"rate-{index}",
            confirmed=True,
            rate=rate,
        )
        assert state["state"] == expected
        assert state["id"] == connection_id
        assert state["generated"] == state["imported"] == 0
        if rate is not None:
            assert state["rate"] == rate


def test_connect_adds_the_discount_term_and_controls_manage_both_schedules(
    session, scheduled_owner, monkeypatch
):
    """Feature 168 FR-007, FR-019: one term prerequisite, two schedules, one set of controls."""
    from reality.db.core import PaymentTerm
    from reality.db.demo_data import DemoDataConnection
    from reality.db.scheduled_jobs import ScheduledJob
    from reality.demo.international import DEMO_DATA_PAYMENT_TERM
    from reality.services import demo_data

    actor = scheduled_owner.id
    tenant = company_setup.create_company(
        session, actor, "two-streams", "Two Streams", "sandbox", "empty", confirmed=True
    )["tenant_id"]
    preview = demo_data.preview(session, tenant, actor)
    assert preview["add"]["payment_terms"] == [DEMO_DATA_PAYMENT_TERM]
    connected = demo_data.connect(
        session, tenant, actor, "c", preview["fingerprint"], confirmed=True
    )
    term = session.scalar(
        select(PaymentTerm).where(
            PaymentTerm.tenant_id == tenant,
            PaymentTerm.code == DEMO_DATA_PAYMENT_TERM["code"],
        )
    )
    assert term.due_days == 14 and term.discount_days == 7
    assert str(term.discount_percent).rstrip("0").rstrip(".") == "2"
    again = demo_data.preview(session, tenant, actor)
    assert again["add"]["payment_terms"] == []
    assert again["references"]["payment_terms"] == {term.code: term.id}
    assert connected["settlement_schedule_id"] is None

    def schedules(status):
        order = record_by_id(session, ScheduledJob, status["schedule_id"])
        settlement = record_by_id(
            session, ScheduledJob, status["settlement_schedule_id"]
        )
        session.refresh(order)
        session.refresh(settlement)
        return order, settlement

    started = demo_data.control(
        session, tenant, actor, "start", connected["revision"], "s1", confirmed=True
    )
    order, settlement = schedules(started)
    assert settlement.job_type == "demo.settle_orders"
    assert settlement.interval_seconds == 60 and settlement.enabled
    assert settlement.configuration["arguments"]["connection_id"] == started["id"]
    assert "seed" not in settlement.configuration["arguments"]
    assert order.enabled and started["order_to_cash"]["next_settlement"] is not None
    paused = demo_data.control(
        session, tenant, actor, "pause", started["revision"], "p1", confirmed=True
    )
    order, settlement = schedules(paused)
    assert not order.enabled and not settlement.enabled
    assert paused["order_to_cash"]["next_settlement"] is None
    resumed = demo_data.control(
        session, tenant, actor, "resume", paused["revision"], "r1", confirmed=True
    )
    order, settlement = schedules(resumed)
    assert order.enabled and settlement.enabled
    settlement_revision = settlement.revision
    faster = demo_data.control(
        session,
        tenant,
        actor,
        "set_rate",
        resumed["revision"],
        "f1",
        confirmed=True,
        rate=300,
    )
    order, settlement = schedules(faster)
    assert order.interval_seconds == 12
    assert settlement.interval_seconds == 60
    assert settlement.revision == settlement_revision
    assert faster["settlement_schedule_id"] == started["settlement_schedule_id"]
    stopped = demo_data.control(
        session, tenant, actor, "stop", faster["revision"], "x1", confirmed=True
    )
    order, settlement = schedules(stopped)
    assert not order.enabled and not settlement.enabled
    # A connection that predates the feature carries no settlement schedule; its
    # next start creates one.
    connection = record_by_id(session, DemoDataConnection, stopped["id"])
    connection.settlement_schedule_id = None
    session.flush()
    restarted = demo_data.control(
        session, tenant, actor, "start", stopped["revision"], "s2", confirmed=True
    )
    assert restarted["settlement_schedule_id"] not in {
        None,
        started["settlement_schedule_id"],
    }
    assert restarted["schedule_id"] != started["schedule_id"]
    disconnected = demo_data.control(
        session,
        tenant,
        actor,
        "disconnect",
        restarted["revision"],
        "d1",
        confirmed=True,
    )
    order, settlement = schedules(disconnected)
    assert not order.enabled and not settlement.enabled


def test_status_reports_order_to_cash_observations(
    session, scheduled_owner, monkeypatch
):
    """Feature 168 FR-023: the block exists with zeros before anything settled."""
    from reality.services import demo_data

    actor = scheduled_owner.id
    tenant = company_setup.create_company(
        session, actor, "o2c-status", "Status", "sandbox", "empty", confirmed=True
    )["tenant_id"]
    connected = demo_data.connect(
        session,
        tenant,
        actor,
        "c",
        demo_data.preview(session, tenant, actor)["fingerprint"],
        confirmed=True,
    )
    block = connected["order_to_cash"]
    assert block == {
        "invoices_issued": 0,
        "payments_received": 0,
        "payments_allocated": 0,
        "invoices_settled": 0,
        "open_residuals": 0,
        "credit_created": "0",
        "unmatched_payments": 0,
        "failed": 0,
        "last_settlement": None,
        "next_settlement": None,
    }
