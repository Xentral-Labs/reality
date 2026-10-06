"""Live-world and local-mail contracts, no provider or model required."""

import pytest
from sqlalchemy import select

from reality.db.core import SourceRecord, now
from reality.services import live_company


def test_manual_preview_and_dedup(session, business, scheduled_owner):
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="live-test",
        confirmed=True,
    )
    assert "seed" not in run["configuration"]
    assert "seed" not in live_company.live_view(
        session, business.tenant.id, run["run_id"]
    )
    args = {
        "kind": "customer_email",
        "party_id": business.customer.id,
        "subject": "Status?",
        "body": "Please update me.",
    }
    before = list(session.scalars(select(SourceRecord.id)))
    assert (
        live_company.preview_event(session, business.tenant.id, run["run_id"], args)[
            "subject"
        ]
        == "Status?"
    )
    assert list(session.scalars(select(SourceRecord.id))) == before
    first = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        args,
        request_id="manual",
        confirmed=True,
    )
    assert first["actor_id"] == scheduled_owner.id
    assert (
        live_company.inject(
            session,
            business.tenant.id,
            scheduled_owner.id,
            run["run_id"],
            args,
            request_id="manual",
            confirmed=True,
        )
        == first
    )
    with pytest.raises(ValueError):
        live_company.inject(
            session,
            business.tenant.id,
            scheduled_owner.id,
            run["run_id"],
            {**args, "body": "changed"},
            request_id="manual",
            confirmed=True,
        )


def test_tick_reply_and_ack(session, business, scheduled_owner):
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="live-test",
        confirmed=True,
    )
    receipt = live_company.tick(
        session, business.tenant.id, run["run_id"], "occurrence-1", now()
    )
    assert receipt["generated"] == 1
    assert (
        live_company.tick(
            session, business.tenant.id, run["run_id"], "occurrence-1", now()
        )
        == receipt
    )
    mail = live_company.inbox(session, business.tenant.id, run["run_id"])
    assert len(mail) == 1
    reply = live_company.reply(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        mail[0]["source_record_id"],
        "We are reviewing it.",
        request_id="reply-1",
        confirmed=True,
    )
    assert reply["status"] == "simulated"
    live_company.acknowledge(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        mail[0]["source_record_id"],
        confirmed=True,
    )
    assert live_company.inbox(session, business.tenant.id, run["run_id"]) == []
    assert (
        live_company.monitor(session, business.tenant.id, run["run_id"])["core_status"]
        == "passed"
    )
    with pytest.raises(Exception, match="not found"):
        live_company.inbox(session, "other-company", run["run_id"])


@pytest.mark.parametrize("supplier_variant", [0, 1, 2])
def test_job_transaction_is_atomic_and_external_purchase_reacts(
    session, business, scheduled_owner, monkeypatch, supplier_variant
):
    from datetime import timedelta

    from reality.services import core, live_company_mail

    monkeypatch.setattr(live_company_mail, "case_variant", lambda key: supplier_variant)
    actual_now = now()
    monkeypatch.setattr(live_company, "now", lambda: actual_now - timedelta(minutes=10))
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="atomic",
        confirmed=True,
    )

    monkeypatch.setattr(live_company, "now", now)

    def forbidden_commit():
        raise AssertionError("Handler must leave commit to the shared worker")

    monkeypatch.setattr(session, "commit", forbidden_commit)
    live_company.tick(session, business.tenant.id, run["run_id"], "atomic-1", now())
    _, _purchase, _, _ = core.create_manual_order(
        session,
        business.tenant.id,
        "purchase",
        "PO-live",
        business.company.id,
        business.supplier.id,
        business.location.id,
        [{"item_id": business.item.id, "quantity": "8", "gross_amount": "40"}],
        "40",
        ordered_at=now() - timedelta(minutes=8),
        _commit=False,
    )
    purchase_source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == business.tenant.id,
            SourceRecord.id == _purchase.source_record_id,
        )
    )
    purchase_source.received_at = now() - timedelta(minutes=8)
    session.flush()
    at = now()
    reaction = live_company.reactions(session, business.tenant.id, run["run_id"], at)
    assert reaction["receipts"] == 1
    assert core.stock_at(session, business.tenant.id, business.item.id) == 4
    assert (
        live_company.reactions(session, business.tenant.id, run["run_id"], at)[
            "receipts"
        ]
        == 0
    )
    confirmation = next(
        m
        for m in live_company.inbox(session, business.tenant.id, run["run_id"])
        if m["subject"] == "Purchase confirmed"
    )
    assert "PO-live" in confirmation["body"] and "8" in confirmation["body"]
    assert "split delivery" in confirmation["body"]
    assert confirmation["case_family"] == "supplier_partial_delivery_confirmation"
    family = [
        "supplier_receiving_hours_query",
        "supplier_priority_quantity_query",
        "supplier_packaging_query",
    ][supplier_variant]
    questions = [
        m
        for m in live_company.inbox(
            session, business.tenant.id, run["run_id"], include_acknowledged=True
        )
        if m.get("case_family") == family
    ]
    assert len(questions) == 1
    assert questions[0]["document_id"] == _purchase.id
    assert "PO-live" in questions[0]["body"] and "8" in questions[0]["body"]


def test_monitor_corruption_and_manual_context_refusal(
    session, business, scheduled_owner, monkeypatch
):
    from reality.services import core

    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="monitor",
        confirmed=True,
    )
    live_company.tick(session, business.tenant.id, run["run_id"], "one", now())
    monkeypatch.setattr(core, "stock_at", lambda *args: 999)
    report = live_company.monitor(session, business.tenant.id, run["run_id"])
    assert report["core_status"] == "failed"
    assert report["differences"]
    live_company.save_monitor(
        session, business.tenant.id, run["run_id"], "fault", now()
    )
    from reality.db.scheduled_jobs import ScheduledJob

    assert all(
        not row.enabled
        for row in session.scalars(
            select(ScheduledJob).where(
                ScheduledJob.tenant_id == business.tenant.id,
                ScheduledJob.job_type.in_(["simulator.world", "simulator.reactions"]),
            )
        )
    )
    with pytest.raises(ValueError):
        live_company.preview_event(
            session,
            business.tenant.id,
            run["run_id"],
            {"kind": "supplier_delay", "party_id": business.customer.id},
        )


def test_live_http_refuses_cross_origin_and_preview_writes_nothing(
    session, business, scheduled_owner
):
    from http.client import HTTPConnection
    from threading import Thread

    from scenarios.company_simulator.live_web import make_live_server

    # Separate Session sees existing committed savepoints through the same test connection.
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="http",
        confirmed=True,
    )
    session.commit()
    with make_live_server(
        session.bind, business.tenant.id, scheduled_owner.id, run["run_id"], 0
    ) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        connection = HTTPConnection("127.0.0.1", server.server_port)
        connection.request(
            "POST", "/api/inject", body="{}", headers={"Origin": "https://evil.invalid"}
        )
        assert connection.getresponse().status == 403
        connection.close()
        server.shutdown()
        thread.join()


def test_live_browser_manual_mail(session, business, scheduled_owner):
    import os
    import subprocess
    from datetime import timedelta
    from pathlib import Path
    from threading import Thread

    from scenarios.company_simulator.live_web import make_live_server

    if not os.environ.get("PLAYWRIGHT_MODULE"):
        pytest.skip("Set PLAYWRIGHT_MODULE for the live Chromium proof")
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="browser",
        confirmed=True,
    )
    from reality.services.live_company_purchasing import prepare

    prepare(
        session, business.tenant.id, scheduled_owner.id, run["run_id"], confirmed=True
    )
    live_company.tick(session, business.tenant.id, run["run_id"], "first", now())
    live_company.reactions(
        session, business.tenant.id, run["run_id"], now() + timedelta(minutes=9)
    )
    first_message = live_company.inbox(session, business.tenant.id, run["run_id"])[0]
    live_company.reply(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        first_message["source_record_id"],
        "We have recorded your order. Dispatch has not been booked yet; we will confirm the actual shipment separately.",
        request_id="browser-real-reply",
        confirmed=True,
    )
    session.commit()
    with make_live_server(
        session.bind, business.tenant.id, scheduled_owner.id, run["run_id"], 0
    ) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            env = {
                **os.environ,
                "SIMULATOR_LIVE_URL": f"http://127.0.0.1:{server.server_port}",
            }
            result = subprocess.run(
                [
                    "node",
                    str(
                        Path(__file__).parents[2]
                        / "scenarios/company_simulator/viewer/live_browser_check.cjs"
                    ),
                ],
                check=False,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
            )
            assert result.returncode == 0, result.stdout + result.stderr
        finally:
            server.shutdown()
            thread.join()


def test_committed_cross_connection_and_restart_visibility():
    """Use a separate disposable database, not a shared test savepoint."""
    from decimal import Decimal
    from uuid import uuid4

    from conftest import admin_engine, admin_url
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from reality.db.core import AppUser, Base, uid
    from reality.db.search_sql import install_search_support
    from scenarios.company_simulator.live import bootstrap

    database = "reality_live_" + uuid4().hex[:10]
    with admin_engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{database}"'))
    engine = create_engine(admin_url.set(database=database))
    try:
        Base.metadata.create_all(engine)
        with engine.begin() as connection:
            install_search_support(connection)
        with Session(engine, expire_on_commit=False) as writer:
            owner = AppUser(
                id=uid("usr"),
                email=uid("test") + "@example.invalid",
                password_hash="unused",
                status="active",
                email_verified_at=now(),
            )
            writer.add(owner)
            writer.commit()
            tenant = bootstrap(writer, owner.id, "cross-connection")
            run = live_company.start(
                writer, tenant, owner.id, request_id="cross-connection", confirmed=True
            )
            from reality.services import scheduled_jobs as jobs
            from reality.services.live_company_purchasing import prepare

            catalogue = prepare(writer, tenant, owner.id, run["run_id"], confirmed=True)
            assert {i["sku"]: Decimal(i["unit_price"]) for i in catalogue["items"]} == {
                "A": Decimal(5),
                "B": Decimal(6),
            }
            assert catalogue == prepare(
                writer, tenant, owner.id, run["run_id"], confirmed=True
            )
            writer.commit()
            queued = jobs.create_manual_run(
                writer,
                tenant,
                owner.id,
                "simulator.world",
                {"run_id": run["run_id"]},
                request_id="cross-connection-world",
            )
            writer.commit()
            claim = jobs.claim_next(writer, tenant)
            assert claim.id == queued.id
            assert (
                jobs.execute_claim(writer, tenant, claim.id, claim.claim_token)
                == "succeeded"
            )
            occurrence = queued.id
            writer.commit()
            with Session(engine) as reader:
                assert len(live_company.inbox(reader, tenant, run["run_id"])) == 1
                assert (
                    live_company.monitor(reader, tenant, run["run_id"])["core_status"]
                    == "passed"
                )
        with Session(engine) as restarted:
            assert (
                live_company.tick(restarted, tenant, run["run_id"], occurrence, now())[
                    "generated"
                ]
                == 1
            )
            restarted.commit()
            assert len(live_company.inbox(restarted, tenant, run["run_id"])) == 1
    finally:
        engine.dispose()
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname=:name AND pid<>pg_backend_pid()"
                ),
                {"name": database},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database}"'))


def test_rate_cursor_report_retry_and_end(session, business, scheduled_owner):
    from datetime import timedelta

    from reality.db.scheduled_jobs import ScheduledJob

    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="timing",
        rate=200,
        confirmed=True,
    )
    schedules = list(
        session.scalars(
            select(ScheduledJob).where(ScheduledJob.tenant_id == business.tenant.id)
        )
    )
    world = next(s for s in schedules if s.job_type == "simulator.world")
    assert world.interval_seconds == 18
    for occurrence in ["a", "b"]:
        live_company.tick(session, business.tenant.id, run["run_id"], occurrence, now())
    first = live_company.inbox(session, business.tenant.id, run["run_id"], limit=1)[0]
    rest = live_company.inbox(
        session, business.tenant.id, run["run_id"], cursor=first["source_record_id"]
    )
    assert len(rest) == 1 and rest[0]["source_record_id"] != first["source_record_id"]
    report = live_company.save_monitor(
        session, business.tenant.id, run["run_id"], "report", now()
    )
    assert (
        live_company.save_monitor(
            session, business.tenant.id, run["run_id"], "report", now()
        )
        == report
    )
    assert report["automatic_orders_last_hour"] == 2
    three_hours = __import__("datetime").datetime.fromisoformat(
        run["configuration"]["started_at"]
    ) + timedelta(hours=3)
    for key in ["three-hours-a", "three-hours-b"]:
        live_company.save_monitor(
            session, business.tenant.id, run["run_id"], key, three_hours
        )
    retained = list(
        session.scalars(
            select(SourceRecord).where(
                SourceRecord.tenant_id == business.tenant.id,
                SourceRecord.source_system == live_company._namespace(run["run_id"]),
                SourceRecord.source_type == "three_hour_report",
            )
        )
    )
    assert len(retained) == 1 and retained[0].external_id == "1"
    end = __import__("datetime").datetime.fromisoformat(run["configuration"]["ends_at"])
    assert live_company.tick(
        session, business.tenant.id, run["run_id"], "end", end + timedelta(seconds=1)
    )["ended"]
    assert all(not s.enabled for s in schedules)


def test_arrival_requires_dispatch_and_goals_require_destination(
    session, business, scheduled_owner, monkeypatch
):
    from datetime import timedelta

    from reality.db.core import Commitment, DocumentLine, ShipmentEvent
    from reality.services import core, shipments

    actual_now = now()
    monkeypatch.setattr(live_company, "now", lambda: actual_now - timedelta(minutes=10))
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="arrival",
        confirmed=True,
    )
    monkeypatch.setattr(live_company, "now", now)
    source = live_company._store(
        session, business.tenant.id, "test", "opening", "opening", {"quantity": "20"}
    )
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
        source_record_id=source.id,
        occurred_at=actual_now - timedelta(minutes=6),
        _commit=False,
    )
    mail = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 2,
            "amount": "20",
        },
        request_id="demand",
        confirmed=True,
        at=actual_now - timedelta(minutes=5),
    )
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == business.tenant.id,
            Commitment.document_line_id.in_(
                select(DocumentLine.id).where(
                    DocumentLine.document_id == mail["document_id"]
                )
            ),
        )
    )
    # An announcement is not physical dispatch, even when its source is old.
    notice, _, _ = shipments.record_shipment_notice(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
        carrier="Simulated carrier",
        occurred_at=actual_now - timedelta(minutes=4),
        commit=False,
    )
    notice.created_at = actual_now - timedelta(minutes=4)
    session.flush()
    assert (
        live_company.reactions(session, business.tenant.id, run["run_id"], actual_now)[
            "arrivals"
        ]
        == 0
    )
    core.reserve(session, business.tenant.id, commitment.id, _commit=False)
    receipt = shipments.record_packaged_execution(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
        carrier="Simulated carrier",
        occurred_at=actual_now - timedelta(minutes=3),
        movements=[
            {
                "commitment_id": commitment.id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "2",
            }
        ],
        commit=False,
    )
    from reality.db.core import Shipment

    dispatch = session.get(Shipment, (business.tenant.id, receipt["shipment_id"]))
    dispatch.created_at = actual_now - timedelta(minutes=3)
    session.flush()
    assert (
        live_company.reactions(session, business.tenant.id, run["run_id"], actual_now)[
            "arrivals"
        ]
        == 0
    )
    handover = session.scalar(
        select(ShipmentEvent).where(
            ShipmentEvent.tenant_id == business.tenant.id,
            ShipmentEvent.shipment_id == dispatch.id,
            ShipmentEvent.event_type == "handed_over",
        )
    )
    assert handover is not None and handover.occurred_at == actual_now
    assert (
        live_company.reactions(
            session,
            business.tenant.id,
            run["run_id"],
            actual_now + timedelta(minutes=1),
        )["arrivals"]
        == 1
    )
    report = live_company.monitor(session, business.tenant.id, run["run_id"])
    assert report["core_status"] == "passed"
    assert report["delivery_goals"] == {"wrong_recipient_or_destination": 1}
    assert (
        session.scalar(
            select(ShipmentEvent.id).where(
                ShipmentEvent.tenant_id == business.tenant.id,
                ShipmentEvent.shipment_id == notice.id,
                ShipmentEvent.event_type == "delivered",
            )
        )
        is None
    )


def test_late_scheduled_occurrence_uses_actual_world_release(
    session, business, scheduled_owner
):
    from datetime import timedelta
    from types import SimpleNamespace

    from reality.jobs.handlers.live_company import LiveConfig, generate

    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="late-release",
        confirmed=True,
    )
    before = now()
    generate(
        session,
        SimpleNamespace(
            tenant_id=business.tenant.id,
            run_id="late-occurrence",
            scheduled_for=before - timedelta(hours=6),
        ),
        LiveConfig(run_id=run["run_id"]),
    )
    mail = live_company.inbox(session, business.tenant.id, run["run_id"])[0]
    from datetime import datetime

    assert datetime.fromisoformat(mail["released_at"]) >= before


def test_staged_customer_mail_is_concrete_and_partial_cancel_is_only_a_request(
    session, business, scheduled_owner, monkeypatch
):
    from datetime import timedelta

    from reality.services import live_company_mail

    at = now()
    monkeypatch.setattr(live_company, "now", lambda: at - timedelta(minutes=15))
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="conversation",
        confirmed=True,
    )
    monkeypatch.setattr(live_company, "now", now)
    mail = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 3,
            "amount": "30",
        },
        request_id="conversation-order",
        confirmed=True,
    )
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == business.tenant.id,
            SourceRecord.id == mail["source_record_id"],
        )
    )
    source.received_at = at - timedelta(minutes=9)
    session.flush()
    monkeypatch.setattr(live_company_mail, "case_variant", lambda key: 0)
    from reality.services import core

    before = core.commitment_terms(session, business.tenant.id)
    live_company.reactions(session, business.tenant.id, run["run_id"], at)
    messages = live_company.inbox(
        session, business.tenant.id, run["run_id"], include_acknowledged=True
    )
    assert len(messages) == 4
    cancel = next(m for m in messages if m["kind"] == "cancellation")
    assert cancel["requested_quantity"] == "1"
    assert "1 of the 3" in cancel["body"]
    assert "keep the other 2" in cancel["body"]
    assert cancel["original_message_source_id"] == source.id
    assert cancel["thread_id"] == mail["thread_id"]
    assert core.commitment_terms(session, business.tenant.id) == before
    live_company.reactions(session, business.tenant.id, run["run_id"], at)
    assert (
        len(
            live_company.inbox(
                session, business.tenant.id, run["run_id"], include_acknowledged=True
            )
        )
        == 4
    )
    view = live_company.live_view(session, business.tenant.id, run["run_id"])
    assert view["party_summaries"][business.customer.id]["incoming"] == 4
    assert view["documents"][0]["id"] == mail["document_id"]
    assert any(
        row["category"] == "incoming" and row["kind"] == "cancellation"
        for row in view["flow"]
    )


def test_shipping_performance_counts_backlog_partial_complete_and_cancelled(
    session, business, scheduled_owner, monkeypatch
):
    from datetime import timedelta

    from reality.db.core import Commitment
    from reality.db.core import now as clock
    from reality.services import core

    at = clock()
    monkeypatch.setattr(live_company, "now", lambda: at - timedelta(minutes=30))
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="performance",
        confirmed=True,
    )
    monkeypatch.setattr(live_company, "now", now)
    original = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 3,
            "amount": "30",
        },
        request_id="performance-order",
        confirmed=True,
    )
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == business.tenant.id,
            SourceRecord.id == original["source_record_id"],
        )
    )
    source.received_at = at - timedelta(minutes=20)
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == business.tenant.id,
            Commitment.document_id == original["document_id"],
        )
    )
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
        occurred_at=at - timedelta(minutes=25),
        _commit=False,
    )
    session.flush()
    metrics = live_company.live_view(session, business.tenant.id, run["run_id"])[
        "performance"
    ]
    assert metrics["unshipped_orders"] == 1 and metrics["open_units"] == "3.0000"
    assert metrics["average_complete_dispatch_minutes"] is None
    core.reserve(session, business.tenant.id, commitment.id, _commit=False)
    metrics = live_company.live_view(session, business.tenant.id, run["run_id"])[
        "performance"
    ]
    assert metrics["ready_orders"] == 1 and metrics["reservation_blocked_orders"] == 0
    reservation_events = [
        e
        for e in live_company.live_view(session, business.tenant.id, run["run_id"])[
            "flow"
        ]
        if e.get("event_type") == "reservation.created"
    ]
    assert (
        reservation_events
        and reservation_events[0]["document_id"] == original["document_id"]
    )
    assert reservation_events[0]["party_id"] == business.customer.id
    core.hold_commitment(
        session, business.tenant.id, commitment.id, "manual_review", _commit=False
    )
    metrics = live_company.live_view(session, business.tenant.id, run["run_id"])[
        "performance"
    ]
    assert metrics["ready_orders"] == 0 and metrics["held_orders"] == 1
    core.release_commitment_hold(
        session, business.tenant.id, commitment.id, _commit=False
    )
    core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        1,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=at - timedelta(minutes=15),
        _commit=False,
    )
    metrics = live_company.live_view(session, business.tenant.id, run["run_id"])[
        "performance"
    ]
    assert metrics["partial_orders"] == 1 and metrics["complete_dispatch_orders"] == 0
    assert metrics["average_first_dispatch_minutes"] == 5
    samples = live_company.live_view(
        session,
        business.tenant.id,
        run["run_id"],
        performance_filter="first_dispatch_sample",
    )["performance"]["orders"]
    assert len(samples) == 1 and samples[0]["first_dispatch_minutes"] == 5
    assert samples[0]["complete_dispatch_minutes"] is None
    assert (
        live_company.live_view(
            session,
            business.tenant.id,
            run["run_id"],
            performance_filter="complete_dispatch_sample",
        )["performance"]["orders"]
        == []
    )
    second_shipment = core.record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        2,
        from_location_id=business.location.id,
        commitment_id=commitment.id,
        occurred_at=at - timedelta(minutes=10),
        _commit=False,
    )
    metrics = live_company.live_view(session, business.tenant.id, run["run_id"])[
        "performance"
    ]
    assert (
        metrics["complete_dispatch_orders"] == 1
        and metrics["dispatch_rate_percent"] == 100
    )
    for cohort in (
        "eligible",
        "received_last_hour",
        "completed_last_hour",
        "complete_dispatch_sample",
    ):
        rows = live_company.live_view(
            session, business.tenant.id, run["run_id"], performance_filter=cohort
        )["performance"]["orders"]
        assert len(rows) == 1 and rows[0]["document_id"] == original["document_id"]
        assert rows[0]["complete_dispatch_minutes"] == 10
    assert (
        metrics["average_complete_dispatch_minutes"] == 10
        and metrics["complete_dispatch_sample_orders"] == 1
    )
    other = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 2,
            "amount": "20",
        },
        request_id="cancelled-order",
        confirmed=True,
    )
    cancellation = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == business.tenant.id,
            Commitment.document_id == other["document_id"],
        )
    )
    core.cancel_commitment(
        session,
        business.tenant.id,
        cancellation.id,
        reason="Customer cancellation",
        _commit=False,
    )
    metrics = live_company.live_view(session, business.tenant.id, run["run_id"])[
        "performance"
    ]
    assert metrics["cancelled_orders"] == 1 and metrics["eligible_orders"] == 1
    assert metrics["dispatch_rate_percent"] == 100

    core.correct_movement(
        session,
        business.tenant.id,
        second_shipment.id,
        reason="Incorrect shipment evidence",
        _commit=False,
    )
    metrics = live_company.live_view(session, business.tenant.id, run["run_id"])[
        "performance"
    ]
    assert metrics["complete_dispatch_orders"] == 0 and metrics["partial_orders"] == 1
    assert metrics["average_complete_dispatch_minutes"] is None
    from reality.services import business_performance

    assert business_performance.overview(session, "another-company")["order_count"] == 0

    # Legacy source-less orders remain in counts; missing receipt time is unknown.
    from reality.db.core import Document

    document = session.scalar(
        select(Document).where(
            Document.tenant_id == business.tenant.id,
            Document.id == original["document_id"],
        )
    )
    document.source_record_id = None
    session.flush()
    legacy = business_performance.overview(session, business.tenant.id)
    assert legacy["order_count"] == 2 and legacy["unknown_receipt_orders"] == 1
    assert legacy["average_first_dispatch_minutes"] is None


def test_purchasing_prerequisites_resolve_and_replay_without_reset(
    session, business, scheduled_owner
):
    from decimal import Decimal

    from reality.services import core
    from reality.services.live_company_purchasing import prepare

    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="purchasing",
        confirmed=True,
    )
    assert (
        core.resolve_price(
            session,
            business.tenant.id,
            business.supplier.id,
            business.item.id,
            10,
            "purchase",
            "EUR",
            business.item.unit,
        )
        is None
    )
    with pytest.raises(ValueError, match="confirmation"):
        prepare(session, business.tenant.id, scheduled_owner.id, run["run_id"])
    with pytest.raises(core.NotFound):
        prepare(
            session,
            business.tenant.id,
            scheduled_owner.id,
            run["run_id"],
            supplier_id="foreign-supplier",
            confirmed=True,
        )
    before = core.stock_at(session, business.tenant.id, business.item.id)
    first = prepare(
        session, business.tenant.id, scheduled_owner.id, run["run_id"], confirmed=True
    )
    assert first == prepare(
        session, business.tenant.id, scheduled_owner.id, run["run_id"], confirmed=True
    )
    price = core.resolve_price(
        session,
        business.tenant.id,
        business.supplier.id,
        business.item.id,
        10,
        "purchase",
        "EUR",
        business.item.unit,
    )
    assert price and price.unit_price == Decimal(6)
    assert Decimal(first["items"][0]["minimum_quantity"]) == Decimal(10)
    assert first["items"][0]["supplier_id"] == business.supplier.id
    assert first["items"][0]["supplier_item_number"].startswith("SIM-")
    assert core.stock_at(session, business.tenant.id, business.item.id) == before
    view = live_company.live_view(session, business.tenant.id, run["run_id"])
    assert (
        view["purchasing"][0]["items"][0]["price_list_entry_id"]
        == price.price_list_entry_id
    )


def test_purchasing_setup_preserves_an_existing_resolved_price(
    session, business, scheduled_owner
):
    from decimal import Decimal

    from reality.services import core
    from reality.services.live_company_purchasing import prepare

    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="existing-purchasing",
        confirmed=True,
    )
    price_list = core.create_price_list(
        session,
        business.tenant.id,
        "EXISTING",
        "Existing supplier agreement",
        "purchase",
        "EUR",
    )
    core.create_price_list_entry(
        session,
        business.tenant.id,
        price_list.id,
        business.item.id,
        1,
        "3.25",
        business.item.unit,
    )
    core.assign_party_price_list(
        session, business.tenant.id, business.supplier.id, price_list.id
    )
    from reality.services.supplier_item_numbers import set_supplier_item_number
    from reality.services.supplier_item_terms import set_supplier_item_terms

    set_supplier_item_number(
        session,
        business.tenant.id,
        business.supplier.id,
        business.item.id,
        "SUPPLIER-EXISTING",
    )
    set_supplier_item_terms(
        session, business.tenant.id, business.supplier.id, business.item.id, 20, 4
    )
    prepared = prepare(
        session, business.tenant.id, scheduled_owner.id, run["run_id"], confirmed=True
    )
    assert prepared["items"][0]["supplier_item_number"] == "SUPPLIER-EXISTING"
    assert Decimal(prepared["items"][0]["minimum_quantity"]) == Decimal(20)
    assert Decimal(prepared["items"][0]["order_multiple"]) == Decimal(4)
    price = core.resolve_price(
        session,
        business.tenant.id,
        business.supplier.id,
        business.item.id,
        10,
        "purchase",
        "EUR",
        business.item.unit,
    )
    assert (
        price.unit_price == Decimal("3.25")
        and prepared["items"][0]["unit_price"] == "3.2500"
    )


def test_live_order_uses_default_cases_and_respects_takeover(
    session, business, scheduled_owner
):
    from reality.services import core
    from reality.services import operational_cases as cases
    from reality.services.case_action_guards import automated_execution
    from reality.services.memberships import Principal

    tenant = business.tenant.id
    actor = Principal(scheduled_owner.id)
    run = live_company.start(
        session,
        tenant,
        scheduled_owner.id,
        request_id="case-integration",
        confirmed=True,
    )
    assert cases.adoption(session, tenant) is None
    live_company.tick(session, tenant, run["run_id"], "first-case-order", now())
    message = live_company.inbox(session, tenant, run["run_id"])[0]
    document_id = message["document_id"]
    case_ids = cases.object_cases(session, tenant, "document", document_id)
    assert len(case_ids) == 1
    live_company.tick(session, tenant, run["run_id"], "first-case-order", now())
    cases.reconcile_events(session, tenant)
    cases.reconcile_events(session, tenant)
    assert cases.object_cases(session, tenant, "document", document_id) == case_ids
    assert len(cases.list_cases(session, tenant)) == 1
    commitment = next(
        c for c in core.commitments(session, tenant) if c.document_id == document_id
    )
    quantity = core.commitment_quantity(session, tenant, commitment.id)
    cases.takeover(
        session,
        tenant,
        case_ids[0],
        actor,
        expected_revision=1,
        request_key="take-live",
        confirmed=True,
    )
    with (
        automated_execution(session, tenant),
        pytest.raises(core.InvalidOperation, match="manually owned"),
    ):
        core.revise_commitment(session, tenant, commitment.id, quantity=quantity)
    assert core.commitment_quantity(session, tenant, commitment.id) == quantity
    review = cases.handback_preview(session, tenant, case_ids[0])
    cases.handback(
        session,
        tenant,
        case_ids[0],
        actor,
        review_digest=review["digest"],
        request_key="return-live",
        confirmed=True,
    )
    with automated_execution(session, tenant):
        core.revise_commitment(session, tenant, commitment.id, quantity=quantity)
    assert cases.object_cases(session, tenant, "document", document_id) == case_ids


def test_mail_waiting_and_reply_lineage_are_actual_evidence(
    session, business, scheduled_owner
):
    from reality.services.business_performance import overview

    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="mail-cohorts",
        confirmed=True,
    )
    live_company.tick(session, business.tenant.id, run["run_id"], "order", now())
    message = live_company.inbox(session, business.tenant.id, run["run_id"])[0]
    initial = overview(session, business.tenant.id, mail_filter="waiting")
    assert initial["mailbox_counts"] == {"incoming": 1, "waiting": 1, "outgoing": 0}
    live_company.acknowledge(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        message["source_record_id"],
        confirmed=True,
    )
    assert overview(session, business.tenant.id)["mailbox_counts"]["waiting"] == 1
    live_company.reply(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        message["source_record_id"],
        "Dispatch is not booked yet.",
        request_id="actual-mail-reply",
        confirmed=True,
    )
    outgoing = overview(session, business.tenant.id, mail_filter="outgoing")
    assert outgoing["mailbox_counts"] == {"incoming": 1, "waiting": 0, "outgoing": 1}
    assert len(outgoing["messages"]) == 1
    assert (
        outgoing["messages"][0]["original"]["source_record_id"]
        == message["source_record_id"]
    )
    assert outgoing["messages"][0]["original"]["body"] == message["body"]
    incoming = overview(session, business.tenant.id, mail_filter="incoming")[
        "messages"
    ][0]
    assert incoming["reply_recorded"] is True
    assert (
        incoming["replies"][0]["source_record_id"]
        == outgoing["messages"][0]["source_record_id"]
    )
    assert incoming["replies"][0]["body"] == "Dispatch is not booked yet."
    assert (
        overview(session, business.tenant.id, mail_filter="waiting")["messages"] == []
    )


def test_order_progress_has_stable_empty_and_recorded_sections(
    session, business, scheduled_owner
):
    from decimal import Decimal

    from reality.db.core import DocumentLine
    from reality.services import core, shipments
    from reality.services.order_progress import overview
    from reality.web.api import document_inspector

    tenant = business.tenant.id
    run = live_company.start(
        session, tenant, scheduled_owner.id, request_id="order-progress", confirmed=True
    )
    live_company.tick(session, tenant, run["run_id"], "order", now())
    message = live_company.inbox(session, tenant, run["run_id"])[0]
    document_id = message["document_id"]
    initial = overview(session, tenant, document_id)
    assert initial["packages"] == initial["invoices"] == initial["delivery_notes"] == []
    assert Decimal(initial["lines"][0]["fulfilled"]) == 0
    titles = [
        s["title"]
        for s in document_inspector(session, tenant, document_id)["sections"][:5]
    ]
    assert titles == [
        "Order progress",
        "Dispatch",
        "Delivery note",
        "Tracking",
        "Invoices",
    ]
    commitment = next(
        c for c in core.commitments(session, tenant) if c.document_id == document_id
    )
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
        _commit=False,
    )
    core.reserve(session, tenant, commitment.id, _commit=False)
    source, _, _ = core.store_source_record(
        session,
        tenant,
        "test-carrier",
        "shipment",
        "package-1",
        {"delivery_note_number": "DN-001"},
    )
    shipments.record_packaged_execution(
        session,
        tenant,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
        carrier="Test carrier",
        tracking_number="TRACK-001",
        source_record_id=source.id,
        movements=[
            {
                "commitment_id": commitment.id,
                "item_id": business.item.id,
                "quantity": "1",
                "from_location_id": business.location.id,
            }
        ],
        commit=False,
    )
    line = session.scalar(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == document_id
        )
    )
    core.record_sales_invoice(session, tenant, line.id, "1", "10", "INV-001")
    current = overview(session, tenant, document_id)
    assert current["packages"][0]["tracking_number"] == "TRACK-001"
    assert current["delivery_notes"] == [{"number": "DN-001", "source_id": source.id}]
    assert current["invoices"][0]["number"] == "INV-001"
    assert Decimal(current["lines"][0]["fulfilled"]) == 1
    assert [
        s["title"]
        for s in document_inspector(session, tenant, document_id)["sections"][:5]
    ] == titles
    with pytest.raises(core.NotFound):
        overview(session, "foreign-tenant", document_id)


@pytest.mark.parametrize(
    "variant,family",
    [
        (0, "partial_cancellation_request"),
        (1, "destination_confirmation_query"),
        (2, "invoice_copy_query"),
        (3, "full_cancellation_request"),
        (4, "quantity_increase_request"),
        (5, "quantity_reduction_request"),
        (6, "substitute_item_query"),
        (7, "destination_change_request"),
        (8, "urgent_dispatch_request"),
        (9, "split_delivery_request"),
        (10, "payment_confirmation_query"),
        (11, "volume_quote_query"),
    ],
)
def test_early_customer_change_variants_are_real_mail_not_business_effects(
    session, business, scheduled_owner, monkeypatch, variant, family
):
    from datetime import timedelta

    from reality.services import core, live_company_mail

    at = now()
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="rich-mail",
        confirmed=True,
    )
    mail = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 3,
            "amount": "30",
        },
        request_id="rich-order",
        confirmed=True,
    )
    source = session.get(SourceRecord, (business.tenant.id, mail["source_record_id"]))
    source.received_at = at - timedelta(minutes=1)
    session.flush()
    monkeypatch.setattr(live_company_mail, "case_variant", lambda key: variant)
    before = core.commitment_terms(session, business.tenant.id)
    config = live_company._run(session, business.tenant.id, run["run_id"])[1]
    assert (
        live_company_mail.customer_conversations(
            session, business.tenant.id, run["run_id"], config, at
        )
        == 1
    )
    incoming = live_company.inbox(
        session, business.tenant.id, run["run_id"], include_acknowledged=True
    )
    request = next(m for m in incoming if m.get("case_family") == family)
    assert request["document_id"] == mail["document_id"]
    assert request["original_message_source_id"] == source.id
    assert request["thread_id"] == mail["thread_id"]
    assert "3" in request["body"]
    assert core.commitment_terms(session, business.tenant.id) == before
    assert (
        live_company_mail.customer_conversations(
            session, business.tenant.id, run["run_id"], config, at
        )
        == 0
    )
    assert (
        live_company_mail.customer_conversations(
            session,
            business.tenant.id,
            run["run_id"],
            config,
            at + timedelta(minutes=15),
        )
        == 3
    )
    assert (
        live_company_mail.customer_conversations(
            session,
            business.tenant.id,
            run["run_id"],
            config,
            at + timedelta(minutes=15),
        )
        == 0
    )
    assert core.commitment_terms(session, business.tenant.id) == before


@pytest.mark.parametrize("variant", [0, 3, 5])
@pytest.mark.parametrize("state", ["cancelled", "shipped", "partial"])
def test_change_mail_respects_actual_open_quantity(
    session, business, scheduled_owner, monkeypatch, variant, state
):
    from datetime import timedelta
    from decimal import Decimal

    from reality.db.core import Commitment
    from reality.services import core, live_company_mail

    at = now()
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="state-aware-mail",
        confirmed=True,
    )
    mail = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 3,
            "amount": "30",
        },
        request_id="state-aware-order",
        confirmed=True,
    )
    source = session.get(SourceRecord, (business.tenant.id, mail["source_record_id"]))
    source.received_at = at - timedelta(minutes=16)
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == business.tenant.id,
            Commitment.document_id == mail["document_id"],
        )
    )
    if state == "cancelled":
        core.cancel_commitment(
            session,
            business.tenant.id,
            commitment.id,
            reason="Customer cancellation",
            _commit=False,
        )
    else:
        core.record_movement(
            session,
            business.tenant.id,
            "opening_stock",
            business.item.id,
            3,
            to_location_id=business.location.id,
            _commit=False,
        )
        core.reserve(session, business.tenant.id, commitment.id, _commit=False)
        core.record_movement(
            session,
            business.tenant.id,
            "shipment",
            business.item.id,
            3 if state == "shipped" else 2,
            from_location_id=business.location.id,
            commitment_id=commitment.id,
            _commit=False,
        )
    session.flush()
    monkeypatch.setattr(live_company_mail, "case_variant", lambda key: variant)
    config = live_company._run(session, business.tenant.id, run["run_id"])[1]
    before = core.commitment_terms(session, business.tenant.id)
    live_company_mail.customer_conversations(
        session, business.tenant.id, run["run_id"], config, at
    )
    incoming = live_company.inbox(
        session, business.tenant.id, run["run_id"], include_acknowledged=True
    )
    changes = [m for m in incoming if m["kind"] == "cancellation"]
    if state == "partial":
        assert len(changes) == 1 and Decimal(changes[0]["requested_quantity"]) == 1
        assert any(
            m.get("case_family") == "remaining_items_escalation" for m in incoming
        )
    else:
        assert changes == []
        expected = (
            "cancellation_refund_query"
            if state == "cancelled"
            else "post_dispatch_documents_query"
        )
        assert any(m.get("case_family") == expected for m in incoming)
    assert core.commitment_terms(session, business.tenant.id) == before


def test_automatic_order_states_price_local_document_day_and_replays(
    session, business, scheduled_owner, monkeypatch
):
    import json
    from datetime import UTC, date, datetime

    from reality.db.core import Document, DocumentLine
    from reality.services.company_time_zone import set_company_time_zone
    from reality.web.api import tenant_evidence_documents

    instant = datetime(2026, 10, 5, 23, 30, tzinfo=UTC)
    monkeypatch.setattr(live_company, "now", lambda: instant)
    set_company_time_zone(session, business.tenant.id, "Europe/Berlin")
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="complete-live",
        confirmed=True,
    )
    first = live_company.tick(
        session, business.tenant.id, run["run_id"], "complete-order", instant
    )
    mail = live_company.inbox(session, business.tenant.id, run["run_id"])[0]
    document = session.get(Document, (business.tenant.id, mail["document_id"]))
    source = session.get(SourceRecord, (business.tenant.id, document.source_record_id))
    payload = json.loads(source.payload)
    assert document.document_date == date(2026, 10, 6)
    assert document.ordered_at == instant
    line = session.scalar(
        select(DocumentLine).where(DocumentLine.document_id == document.id)
    )
    assert line.unit_price == 10
    assert payload["document_date"] == "2026-10-06"
    assert payload["lines"][0]["unit_price"] == "10"
    rows = tenant_evidence_documents(
        business.tenant.id, session, page=1, size=50, document_type="sales_order"
    )
    assert rows["items"][0]["date"] == "2026-10-06"
    assert (
        live_company.tick(
            session, business.tenant.id, run["run_id"], "complete-order", instant
        )
        == first
    )


@pytest.mark.parametrize("full_mailbox", [False, True])
@pytest.mark.parametrize("corrected", [False, True])
@pytest.mark.parametrize("historical_delivered", [False, True])
def test_carrier_handover_is_source_backed_and_independent_of_mail_pressure(
    session,
    business,
    scheduled_owner,
    monkeypatch,
    full_mailbox,
    corrected,
    historical_delivered,
):
    import json
    from datetime import timedelta

    from reality.db.core import Movement, Shipment, ShipmentEvent
    from reality.services import core, shipments

    at = now()
    monkeypatch.setattr(live_company, "now", lambda: at - timedelta(minutes=10))
    run = live_company.start(
        session,
        business.tenant.id,
        scheduled_owner.id,
        request_id="handover",
        confirmed=True,
    )
    monkeypatch.setattr(live_company, "now", now)
    source = live_company._store(
        session,
        business.tenant.id,
        "test",
        "opening",
        "handover-stock",
        {"quantity": "20"},
    )
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
        source_record_id=source.id,
        occurred_at=at - timedelta(minutes=6),
        _commit=False,
    )
    from reality.db.core import Commitment, DocumentLine

    mail = live_company.inject(
        session,
        business.tenant.id,
        scheduled_owner.id,
        run["run_id"],
        {
            "kind": "order",
            "party_id": business.customer.id,
            "item_id": business.item.id,
            "quantity": 2,
            "amount": "20",
        },
        request_id="handover-demand",
        confirmed=True,
        at=at - timedelta(minutes=5),
    )
    commitment = session.scalar(
        select(Commitment).where(
            Commitment.tenant_id == business.tenant.id,
            Commitment.document_line_id.in_(
                select(DocumentLine.id).where(
                    DocumentLine.tenant_id == business.tenant.id,
                    DocumentLine.document_id == mail["document_id"],
                )
            ),
        )
    )
    core.reserve(session, business.tenant.id, commitment.id, _commit=False)
    receipt = shipments.record_packaged_execution(
        session,
        business.tenant.id,
        direction="outbound",
        purpose="customer_delivery",
        counterparty_id=business.customer.id,
        carrier="Simulated carrier",
        occurred_at=at - timedelta(minutes=3),
        movements=[
            {
                "commitment_id": commitment.id,
                "item_id": business.item.id,
                "from_location_id": business.location.id,
                "quantity": "2",
            }
        ],
        commit=False,
    )
    shipment = session.get(Shipment, (business.tenant.id, receipt["shipment_id"]))
    shipment.created_at = at - timedelta(minutes=3)
    if corrected:
        movement = session.scalar(
            select(Movement).where(
                Movement.tenant_id == business.tenant.id,
                Movement.shipment_package_id == receipt["package_id"],
                Movement.type == "shipment",
            )
        )
        core.correct_movement(
            session,
            business.tenant.id,
            movement.id,
            reason="Retracted physical dispatch",
            _commit=False,
        )
    if historical_delivered:
        shipments.record_shipment_event(
            session,
            business.tenant.id,
            shipment.id,
            event_type="delivered",
            reporter_type="carrier",
            shipment_package_id=receipt["package_id"],
            occurred_at=at - timedelta(minutes=1),
            commit=False,
        )
    session.flush()
    from reality.services.live_company_carrier import observe_carrier

    assert (
        observe_carrier(
            session, business.tenant.id, "other-run", at - timedelta(minutes=10), at
        )
        == 0
    )
    blocked = corrected or historical_delivered
    if full_mailbox:
        monkeypatch.setattr(live_company, "inbox", lambda *args, **kwargs: [{}] * 2000)
    before_mail = len(
        list(
            session.scalars(
                select(SourceRecord.id).where(
                    SourceRecord.tenant_id == business.tenant.id,
                    SourceRecord.source_type == "incoming",
                )
            )
        )
    )
    result = live_company.reactions(session, business.tenant.id, run["run_id"], at)
    assert result["arrivals"] == 0
    events = list(
        session.scalars(
            select(ShipmentEvent).where(
                ShipmentEvent.tenant_id == business.tenant.id,
                ShipmentEvent.shipment_id == shipment.id,
                ShipmentEvent.event_type == "handed_over",
            )
        )
    )
    assert len(events) == (0 if blocked else 1)
    if not blocked:
        event = events[0]
        assert event.occurred_at == at and event.reporter_type == "carrier"
        evidence = session.get(
            SourceRecord, (business.tenant.id, event.source_record_id)
        )
        payload = json.loads(evidence.payload)
        assert payload["origin"] == "simulated_carrier"
        assert payload["occurred_at"] == at.isoformat()
        assert payload["package_id"] == receipt["package_id"]
    live_company.reactions(session, business.tenant.id, run["run_id"], at)
    assert len(
        list(
            session.scalars(
                select(ShipmentEvent.id).where(
                    ShipmentEvent.tenant_id == business.tenant.id,
                    ShipmentEvent.shipment_id == shipment.id,
                    ShipmentEvent.event_type == "handed_over",
                )
            )
        )
    ) == (0 if blocked else 1)
    result = live_company.reactions(
        session, business.tenant.id, run["run_id"], at + timedelta(minutes=1)
    )
    assert result["arrivals"] == (0 if blocked else 1)
    if full_mailbox:
        assert (
            len(
                list(
                    session.scalars(
                        select(SourceRecord.id).where(
                            SourceRecord.tenant_id == business.tenant.id,
                            SourceRecord.source_type == "incoming",
                        )
                    )
                )
            )
            == before_mail
        )
    with pytest.raises(core.NotFound):
        live_company.reactions(session, "other-company", run["run_id"], at)
    event_count = len(
        list(
            session.scalars(
                select(ShipmentEvent.id).where(
                    ShipmentEvent.tenant_id == business.tenant.id
                )
            )
        )
    )
    assert (
        live_company.reactions(
            session, business.tenant.id, run["run_id"], at + timedelta(hours=73)
        )["arrivals"]
        == 0
    )
    assert (
        len(
            list(
                session.scalars(
                    select(ShipmentEvent.id).where(
                        ShipmentEvent.tenant_id == business.tenant.id
                    )
                )
            )
        )
        == event_count
    )
