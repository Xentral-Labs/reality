"""Independent legacy reconciliation and bounded disposable-cache recovery."""

from sqlalchemy import select

from reality.db.core import BusinessEvent, SourceRecord, now
from reality.services import business_performance, business_projection, core


def drain(session, tenant, *, force=False):
    for i in range(1000):
        business_projection.refresh(session, tenant, force=force and i == 0)
        session.flush()
        data = business_projection.overview(session, tenant)
        if data["processing"]["state"] == "ready":
            return data
    raise AssertionError("projection did not converge")


def test_cold_reads_do_not_build(session, business):
    data = business_projection.overview(session, business.tenant.id)
    assert data["processing"]["state"] == "uninitialized"
    assert data["processing"]["delayed"] is True
    assert data["orders"] == []
    assert not session.new and not session.dirty


def test_empty_oracle_replay_and_tenant_scope(session, business):
    tenant = business.tenant.id
    expected = business_performance.overview(session, tenant)
    actual = drain(session, tenant)
    for key in business_projection.ORDER_COUNTERS:
        assert actual[key] == expected[key]
    assert actual["mailbox_counts"] == expected["mailbox_counts"]
    before = actual.copy()
    actual = drain(session, tenant)
    assert actual["order_count"] == before["order_count"]
    assert business_projection.overview(session, "foreign")["orders"] == []


def test_mail_acknowledgement_is_not_reply(session, business):
    tenant = business.tenant.id
    incoming, _, _ = core.store_source_record(
        session,
        tenant,
        "company_simulator:test",
        "incoming",
        "m1",
        {
            "message_id": "m1",
            "direction": "incoming",
            "subject": "Question",
            "body": "Please reply",
        },
    )
    session.flush()
    actual = drain(session, tenant)
    assert actual["mailbox_counts"] == {"incoming": 1, "waiting": 1, "outgoing": 0}
    core.store_source_record(
        session,
        tenant,
        "company_simulator:test",
        "ack",
        incoming.id,
        {"message_source_id": incoming.id},
    )
    session.flush()
    actual = drain(session, tenant)
    assert actual["mailbox_counts"]["waiting"] == 1
    assert actual["local_unread_messages"] == 0
    assert actual["messages"][0]["work_completed"] is None
    core.store_source_record(
        session,
        tenant,
        "company_simulator:test",
        "outgoing",
        "r1",
        {
            "message_id": "r1",
            "in_reply_to": "m1",
            "direction": "outgoing",
            "subject": "Reply",
            "body": "Recorded answer",
        },
    )
    session.flush()
    actual = drain(session, tenant)
    oracle = business_performance.overview(session, tenant)
    assert actual["mailbox_counts"] == oracle["mailbox_counts"]
    assert actual["local_unread_messages"] == oracle["local_unread_messages"]
    by_id = {r["source_record_id"]: r for r in actual["messages"]}
    for row in oracle["messages"]:
        assert all(
            by_id[row["source_record_id"]][key] == value for key, value in row.items()
        )
    # Duplicate/delayed delivery re-reads current Reality rather than adding twice.
    core.emit_business_event(
        session,
        tenant,
        "source_record.stored",
        "source_record",
        incoming.id,
        {},
        occurred_at=now(),
    )
    session.flush()
    assert drain(session, tenant)["mailbox_counts"] == oracle["mailbox_counts"]
    assert session.scalar(
        select(BusinessEvent.sequence)
        .where(BusinessEvent.tenant_id == tenant)
        .order_by(BusinessEvent.sequence.desc())
        .limit(1)
    )
    assert session.scalar(
        select(SourceRecord.id).where(
            SourceRecord.tenant_id == tenant, SourceRecord.id == incoming.id
        )
    )


def order(session, business, number, quantity=3, due=None):
    document = core.create_document(
        session, business.tenant.id, "sales_order", number, business.customer.id, "30"
    )
    commitment = core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        quantity,
        (due or now()).isoformat(),
        document_id=document.id,
    )
    return document, commitment


def reconcile(session, tenant):
    session.flush()
    actual = drain(session, tenant)
    expected = business_performance.overview(session, tenant)
    for key in (
        *business_projection.ORDER_COUNTERS,
        "open_units",
        "dispatch_rate_percent",
        "average_first_dispatch_minutes",
        "average_complete_dispatch_minutes",
    ):
        assert actual[key] == expected[key], key
    for flag in ("", *business_projection.ORDER_FLAGS):
        actual_ids = []
        cursor = ""
        while True:
            page = business_projection.overview(
                session, tenant, order_filter=flag, order_limit=2, order_cursor=cursor
            )
            actual_ids.extend(r["document_id"] for r in page["orders"])
            cursor = page["orders_next_cursor"]
            if not cursor:
                break
        expected_ids = [
            r["document_id"]
            for r in expected["orders"]
            if not flag or flag in r["flags"]
        ]
        assert actual_ids == expected_ids, flag
    return actual


def test_orders_revisions_holds_reservations_correction_and_cancel(session, business):
    from datetime import timedelta

    tenant = business.tenant.id
    doc, promise = order(session, business, "FIRST", due=now() + timedelta(hours=1))
    _, cancelled = order(session, business, "CANCELLED")
    source, _, _ = core.store_source_record(
        session, tenant, "fixture", "order", doc.id, {"number": doc.number}
    )
    source.received_at = now() - timedelta(minutes=30)
    doc.source_record_id = source.id
    session.flush()
    assert reconcile(session, tenant)["at_risk_orders"] == 1
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        10,
        to_location_id=business.location.id,
        _commit=False,
    )
    core.reserve(session, tenant, promise.id, 3, _commit=False)
    assert reconcile(session, tenant)["ready_orders"] == 1
    core.hold_commitment(session, tenant, promise.id, "credit_check", _commit=False)
    assert reconcile(session, tenant)["held_orders"] == 1
    core.release_commitment_hold(session, tenant, promise.id, _commit=False)
    first = core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        1,
        from_location_id=business.location.id,
        commitment_id=promise.id,
        _commit=False,
    )
    assert reconcile(session, tenant)["partial_orders"] == 1
    core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        2,
        from_location_id=business.location.id,
        commitment_id=promise.id,
        _commit=False,
    )
    assert reconcile(session, tenant)["complete_dispatch_orders"] == 1
    core.correct_movement(
        session, tenant, first.id, reason="Wrong evidence", _commit=False
    )
    assert reconcile(session, tenant)["partial_orders"] == 1
    core.cancel_commitment(
        session, tenant, cancelled.id, reason="Cancelled", _commit=False
    )
    assert reconcile(session, tenant)["cancelled_orders"] == 1
    core.revise_commitment(
        session,
        tenant,
        promise.id,
        (now() + timedelta(hours=3)).isoformat(),
        quantity=4,
        note="Changed quantity",
        _commit=False,
    )
    reconcile(session, tenant)


def test_clock_without_events_updates_risk_overdue_hourly(
    session, business, monkeypatch
):
    from datetime import timedelta

    stamp = now()
    tenant = business.tenant.id
    doc, _ = order(session, business, "CLOCK", due=stamp + timedelta(hours=3))
    source, _, _ = core.store_source_record(
        session, tenant, "fixture", "order", doc.id, {}
    )
    source.received_at = stamp
    doc.source_record_id = source.id
    session.flush()
    for module in (business_projection, business_performance):
        monkeypatch.setattr(module, "now", lambda: stamp)
    first = reconcile(session, tenant)
    sequence = first["processing"]["target_event_sequence"]
    assert first["orders_received_last_hour"] == 1 and first["at_risk_orders"] == 0
    stamp += timedelta(hours=1, seconds=1)
    next_data = reconcile(session, tenant)
    assert next_data["processing"]["target_event_sequence"] == sequence
    assert (
        next_data["at_risk_orders"] == 1 and next_data["orders_received_last_hour"] == 0
    )
    stamp += timedelta(hours=2)
    last = reconcile(session, tenant)
    assert last["overdue_orders"] == 1 and last["at_risk_orders"] == 0


def test_bounded_rebuild_keeps_publication_and_catches_interleaved_writes(
    session, business, monkeypatch
):
    monkeypatch.setattr(business_projection, "CHUNK", 2)
    tenant = business.tenant.id
    for n in range(5):
        order(session, business, f"BUILD-{n}")
    session.flush()
    original = reconcile(session, tenant)
    business_projection.refresh(session, tenant, force=True)
    session.flush()
    building = business_projection.overview(session, tenant)
    assert building["order_count"] == original["order_count"] == 5
    assert building["processing"]["state"] == "rebuilding"
    late, promise = order(session, business, "DURING-REBUILD")
    core.cancel_commitment(
        session, tenant, promise.id, reason="During rebuild", _commit=False
    )
    # A fresh Session identity map emulates restart between durable chunks.
    session.flush()
    session.expire_all()
    data = reconcile(session, tenant)
    assert data["order_count"] == 6 and data["cancelled_orders"] == 1
    assert late.id in {r["document_id"] for r in data["orders"]}


def test_cursors_bound_scope_and_rebuild_generation(session, business):
    import pytest

    tenant = business.tenant.id
    for n in range(3):
        order(session, business, f"PAGE-{n}")
    session.flush()
    drain(session, tenant)
    cursor = business_projection.overview(session, tenant, order_limit=1)[
        "orders_next_cursor"
    ]
    assert cursor
    for arguments in ({"order_filter": "ready"}, {"order_cursor": "invalid"}):
        with pytest.raises(ValueError, match="cursor"):
            business_projection.overview(
                session,
                tenant,
                order_cursor=arguments.get("order_cursor", cursor),
                order_filter=arguments.get("order_filter", ""),
            )
    with pytest.raises(ValueError, match="cursor"):
        business_projection.overview(session, "foreign", order_cursor=cursor)
    drain(session, tenant, force=True)
    with pytest.raises(ValueError, match="cursor"):
        business_projection.overview(session, tenant, order_cursor=cursor)


def test_shared_job_discovery_and_read_only_queries(session, business):
    from reality.db.core import ProjectionRow
    from reality.services import projection_jobs, projections

    tenant = business.tenant.id
    assert business_projection.NAME in projection_jobs.due_projections(session, tenant)
    for _ in range(10):
        projections.rebuild_projections(session, tenant, [business_projection.NAME])
        if business_projection.overview(session, tenant)["processing"]["available"]:
            break
    data = business_projection.overview(session, tenant)
    assert data["processing"]["available"]
    before = session.scalar(
        select(ProjectionRow.payload).where(
            ProjectionRow.tenant_id == tenant,
            ProjectionRow.projection_name == business_projection.NAME,
        )
    )
    for _ in range(3):
        business_projection.overview(session, tenant)
    assert before == session.scalar(
        select(ProjectionRow.payload).where(
            ProjectionRow.tenant_id == tenant,
            ProjectionRow.projection_name == business_projection.NAME,
        )
    )
    assert not session.new and not session.dirty


def test_monitor_read_does_not_open_storyline_writer():
    from reality.storyline import recorder

    def forbidden():
        raise AssertionError("Monitoring must not open an extra recording connection")

    recorder.record_http_view(
        forbidden,
        tenant_id="synthetic",
        route="/interactions/business",
        params={},
        status=200,
        duration_ms=1,
    )


def test_real_concurrent_commit_during_repeatable_read_build_and_rollback(
    postgres_database, monkeypatch
):
    """Committed writer proceeds while a chunk holds a stable worker snapshot."""
    from types import SimpleNamespace

    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from reality.db.core import Base
    from reality.services import business_projection_derivation

    engine = create_engine(postgres_database)
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            tenant = core.create_tenant(db, "Disposable concurrent company")
            company = core.create_party(db, tenant.id, "Company", "company")
            customer = core.create_party(db, tenant.id, "Customer", "customer")
            item = core.create_item(db, tenant.id, "TEST", "Test")
            location = core.create_location(db, tenant.id, "Location")
            fixture = SimpleNamespace(
                tenant=tenant,
                company=company,
                customer=customer,
                item=item,
                location=location,
            )
            _, promise = order(db, fixture, "CONCURRENT")
            db.commit()
            tenant_id, commitment_id = tenant.id, promise.id
            drain(db, tenant_id)
            db.commit()
        original = business_projection_derivation.order_rows
        wrote = False

        def concurrent(session, tenant_id, document_ids, observed):
            nonlocal wrote
            result = original(session, tenant_id, document_ids, observed)
            if not wrote:
                wrote = True
                with Session(engine) as writer:
                    core.cancel_commitment(
                        writer,
                        tenant_id,
                        commitment_id,
                        reason="Committed during worker snapshot",
                        _commit=False,
                    )
                    writer.commit()
            return result

        monkeypatch.setattr(business_projection_derivation, "order_rows", concurrent)
        with (
            engine.connect().execution_options(
                isolation_level="REPEATABLE READ"
            ) as connection,
            Session(connection) as worker,
        ):
            business_projection.refresh(worker, tenant_id, force=True)
            worker.commit()
        assert wrote
        with Session(engine) as reader:
            before = business_projection.overview(reader, tenant_id)
            assert before["cancelled_orders"] == 0
            assert before["processing"]["state"] == "pending"
            assert (
                before["processing"]["processed_event_sequence"]
                < before["processing"]["target_event_sequence"]
            )
        # A completed derivation followed by transaction rollback publishes no deltas.
        with Session(engine) as failed:
            business_projection.refresh(failed, tenant_id)
            failed.rollback()
        with Session(engine) as reader:
            assert (
                business_projection.overview(reader, tenant_id)["cancelled_orders"] == 0
            )
            actual = drain(reader, tenant_id)
            assert actual["cancelled_orders"] == 1
            assert actual["order_count"] == 1
            assert (
                actual["open_units"]
                == business_performance.overview(reader, tenant_id)["open_units"]
            )
            reader.commit()
        # Full rebuild after process restart converges to the same authoritative state.
        with Session(engine) as restarted:
            assert drain(restarted, tenant_id, force=True)["cancelled_orders"] == 1
    finally:
        engine.dispose()


def test_migration_roundtrip_indexes_and_unfinished_job_guard(
    postgres_database, monkeypatch
):
    import pytest
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.orm import Session

    from reality.services import projection_jobs

    monkeypatch.setenv("REALITY_DATABASE_URL", postgres_database)
    config = Config("alembic.ini")
    command.upgrade(config, "head")
    engine = create_engine(postgres_database)
    try:
        names = {i["name"] for i in inspect(engine).get_indexes("business_order_row")}
        assert {
            "ix_business_order_page",
            "ix_business_order_clock",
            "ix_business_order_ready",
        } <= names
        assert {"ix_source_business_message_id", "ix_source_business_in_reply_to"} <= {
            i["name"] for i in inspect(engine).get_indexes("source_record")
        }
        command.downgrade(config, "0146_shipping_plan_inputs")
        assert "business_order_row" not in inspect(engine).get_table_names()
        assert "shipping_plan_statement" in inspect(engine).get_table_names()
        command.upgrade(config, "head")
        with Session(engine) as db:
            tenant = core.create_tenant(db, "Disposable migration guard")
            runs = projection_jobs.enqueue_due_projections(db, tenant.id)
            assert any(
                business_projection.NAME in r.configuration["arguments"]["names"]
                for r in runs
            )
            db.commit()
        with pytest.raises(RuntimeError, match="Drain Business"):
            command.downgrade(config, "0146_shipping_plan_inputs")
    finally:
        engine.dispose()


def test_api_owner_boundary_and_page_validation(session, business, monkeypatch):
    from fastapi import HTTPException
    from fastapi.testclient import TestClient

    from reality.web import interactions_api
    from reality.web.api import database_session
    from reality.web.app import app

    tenant = business.tenant.id
    drain(session, tenant)
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            response = client.get(
                f"/api/tenants/{tenant}/interactions/business?order_limit=201"
            )
            assert response.status_code == 422
            response = client.get(
                f"/api/tenants/{tenant}/interactions/business?order_cursor=invalid"
            )
            assert response.status_code == 422
            response = client.get(f"/api/tenants/{tenant}/interactions/business")
            assert (
                response.status_code == 200
                and response.json()["processing"]["available"]
            )

            def revoked(*args):
                raise HTTPException(status_code=404, detail="Not found")

            monkeypatch.setattr(interactions_api, "_owner", revoked)
            denied = client.get(f"/api/tenants/{tenant}/interactions/business")
            assert denied.status_code == 404 and "orders" not in denied.text
    finally:
        app.dependency_overrides.clear()


def test_unread_scope_includes_local_source_without_mail_direction(session, business):
    tenant = business.tenant.id
    core.store_source_record(
        session,
        tenant,
        "company_simulator:unknown",
        "incoming",
        "missing-direction",
        {"message_id": "missing-direction", "body": "Unknown direction"},
    )
    session.flush()
    data = drain(session, tenant)
    oracle = business_performance.overview(session, tenant)
    assert (
        data["mailbox_counts"]
        == oracle["mailbox_counts"]
        == {"incoming": 0, "outgoing": 0, "waiting": 0}
    )
    assert data["local_unread_messages"] == oracle["local_unread_messages"] == 1
    assert data["messages"] == oracle["messages"] == []


def test_long_retained_message_identity_and_version_rebuild(
    session, business, monkeypatch
):
    from reality.services import projections

    tenant = business.tenant.id
    # External identities must never overflow a B-tree index or be truncated.
    identity = "message-" + "abcdef1234567890" * 2000
    incoming, _, _ = core.store_source_record(
        session,
        tenant,
        "company_simulator:long",
        "incoming",
        "request",
        {"message_id": identity, "direction": "incoming", "body": "Question"},
    )
    drain(session, tenant)
    core.store_source_record(
        session,
        tenant,
        "company_simulator:long",
        "outgoing",
        "answer",
        {
            "message_id": "answer",
            "in_reply_to": identity,
            "direction": "outgoing",
            "body": "Answer",
        },
    )
    actual = drain(session, tenant)
    oracle = business_performance.overview(session, tenant)
    assert actual["mailbox_counts"] == oracle["mailbox_counts"]
    assert next(r for r in actual["messages"] if r["source_record_id"] == incoming.id)[
        "reply_recorded"
    ]
    monkeypatch.setattr(
        projections, "PROJECTION_VERSION", projections.PROJECTION_VERSION + 1
    )
    after = drain(session, tenant)
    assert after["mailbox_counts"] == actual["mailbox_counts"]
    assert after["processing"]["projection_version"] == projections.PROJECTION_VERSION


def test_partner_stock_blocks_and_correction_to_another_order(session, business):
    from reality.services.stock_blocks import block_stock, release_stock_block

    tenant = business.tenant.id
    _, first = order(session, business, "CORRECTION-FIRST")
    _, second = order(session, business, "CORRECTION-SECOND")
    core.record_movement(
        session,
        tenant,
        "opening_stock",
        business.item.id,
        20,
        to_location_id=business.location.id,
        _commit=False,
    )
    core.reserve(session, tenant, first.id, 3, _commit=False)
    core.reserve(session, tenant, second.id, 3, _commit=False)
    assert reconcile(session, tenant)["ready_orders"] == 2
    core.hold_party_delivery(
        session, tenant, business.customer.id, "credit_check", _commit=False
    )
    assert reconcile(session, tenant)["held_orders"] == 2
    core.release_party_delivery_hold(session, tenant, business.customer.id)
    assert reconcile(session, tenant)["held_orders"] == 0
    block = block_stock(
        session, tenant, business.item.id, business.location.id, 2, "quality"
    )
    reconcile(session, tenant)
    release_stock_block(session, tenant, block.id, reason="Inspection cleared")
    reconcile(session, tenant)
    shipment = core.record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        1,
        from_location_id=business.location.id,
        commitment_id=first.id,
        _commit=False,
    )
    reconcile(session, tenant)
    core.correct_movement(
        session,
        tenant,
        shipment.id,
        reason="Wrong order",
        replacement={
            "type": "shipment",
            "item_id": business.item.id,
            "quantity": "1",
            "from_location_id": business.location.id,
            "commitment_id": second.id,
        },
        _commit=False,
    )
    result = reconcile(session, tenant)
    by_id = {row["document_id"]: row for row in result["orders"]}
    assert "unshipped" in by_id[first.document_id]["flags"]
    assert "partial" in by_id[second.document_id]["flags"]
    for promise in (first, second):
        core.cancel_commitment(
            session, tenant, promise.id, reason="Fully cancelled", _commit=False
        )
    assert reconcile(session, tenant)["cancelled_orders"] == 2


def test_reply_before_request_and_full_paged_mail_cohorts(session, business):
    tenant = business.tenant.id
    namespace = "company_simulator:paging"
    reply, _, _ = core.store_source_record(
        session,
        tenant,
        namespace,
        "outgoing",
        "early-reply",
        {
            "message_id": "early-reply",
            "in_reply_to": "request-0",
            "direction": "outgoing",
            "body": "Already answered",
        },
    )
    assert drain(session, tenant)["messages"][0]["original"] is None
    for n in range(7):
        core.store_source_record(
            session,
            tenant,
            namespace,
            "incoming",
            f"request-{n}",
            {
                "message_id": f"request-{n}",
                "direction": "incoming",
                "body": f"Question {n}",
            },
        )
    foreign = core.create_tenant(session, "Other synthetic company")
    core.store_source_record(
        session,
        foreign.id,
        namespace,
        "outgoing",
        "foreign-reply",
        {
            "message_id": "foreign-reply",
            "in_reply_to": "request-1",
            "direction": "outgoing",
            "body": "Foreign evidence",
        },
    )
    data = drain(session, tenant)
    oracle = business_performance.overview(session, tenant)
    assert (
        data["mailbox_counts"]
        == oracle["mailbox_counts"]
        == {"incoming": 7, "outgoing": 1, "waiting": 6}
    )
    assert (
        next(row for row in data["messages"] if row["source_record_id"] == reply.id)[
            "original"
        ]
        is not None
    )
    for cohort in ("", "incoming", "outgoing", "waiting"):
        expected = business_performance.overview(session, tenant, mail_filter=cohort)[
            "messages"
        ]
        rows, cursor = [], ""
        while True:
            page = business_projection.overview(
                session, tenant, mail_filter=cohort, mail_limit=2, mail_cursor=cursor
            )
            rows.extend(page["messages"])
            cursor = page["messages_next_cursor"]
            if not cursor:
                break
        assert [row["source_record_id"] for row in rows] == [
            row["source_record_id"] for row in expected
        ]
        for actual, original in zip(rows, expected, strict=True):
            assert all(actual[key] == value for key, value in original.items())


def test_published_read_is_one_cache_statement_without_reality_derivation(
    session, business, monkeypatch
):
    from sqlalchemy import event

    from reality.services import business_projection_derivation as derivation

    document, _ = order(session, business, "PUBLISHED")
    tenant = business.tenant.id
    drain(session, tenant)

    def forbidden(*args, **kwargs):
        raise AssertionError("Dashboard reads must never derive Reality histories")

    for name in ("order_rows", "mail_rows", "auxiliary"):
        monkeypatch.setattr(derivation, name, forbidden)
    monkeypatch.setattr(business_performance, "overview", forbidden)
    monkeypatch.setattr(core, "commitment_terms", forbidden)
    # A read must also leave a caller's pending mutation unflushed.
    document.number = "UNCOMMITTED"
    statements = []
    bind = session.get_bind()

    def capture(connection, cursor, statement, parameters, context, many):
        statements.append(statement)

    event.listen(bind, "before_cursor_execute", capture)
    try:
        data = business_projection.overview(session, tenant)
    finally:
        event.remove(bind, "before_cursor_execute", capture)
    assert data["orders"][0]["number"] == "PUBLISHED"
    assert document in session.dirty
    assert len(statements) == 1 and statements[0].lstrip().startswith("WITH")
    for table in ("source_record", "commitment", "movement", "document "):
        assert f"FROM {table}" not in statements[0]


def test_missing_and_empty_message_ids_reconcile_legacy_sql_cohorts(session, business):
    tenant = business.tenant.id
    namespace = "company_simulator:incomplete"
    for n, payload in enumerate(({}, {"message_id": ""})):
        core.store_source_record(
            session,
            tenant,
            namespace,
            "incoming",
            f"request-{n}",
            {**payload, "direction": "incoming"},
        )
    drain(session, tenant)
    for n, payload in enumerate(({}, {"in_reply_to": ""})):
        core.store_source_record(
            session,
            tenant,
            namespace,
            "outgoing",
            f"reply-{n}",
            {**payload, "direction": "outgoing"},
        )
        data = drain(session, tenant)
        oracle = business_performance.overview(session, tenant)
        assert data["mailbox_counts"] == oracle["mailbox_counts"]
        for actual, expected in zip(data["messages"], oracle["messages"], strict=True):
            assert all(actual[key] == value for key, value in expected.items())
        assert [
            row["source_record_id"]
            for row in business_projection.overview(
                session, tenant, mail_filter="waiting"
            )["messages"]
        ] == [
            row["source_record_id"]
            for row in business_performance.overview(
                session, tenant, mail_filter="waiting"
            )["messages"]
        ]
