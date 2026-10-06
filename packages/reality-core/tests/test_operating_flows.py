"""Independent operational flow observations preserve authority and complete counts."""

from datetime import timedelta

from sqlalchemy import func, select

from reality.db.core import BusinessEvent, SourceRecord, now
from reality.services import core


def observe(session, business, at):
    from reality.services.operating_flows import observe

    return observe(session, business.tenant.id, observed_at=at)


def source(session, business, system, kind, key, payload, at):
    row = core.store_source_record(
        session, business.tenant.id, system, kind, key, payload
    )
    row = row[0]
    row.received_at = at
    session.flush()
    return row


def test_messages_count_full_lineage_not_acknowledgements_or_preview(session, business):
    # BUSINESS PURPOSE: A falling correspondence queue must mean actual replies, not reading or a short preview.
    # BUSINESS RULE: Only same-company/run replies answer a message; duplicates count once and acknowledgements remain separate.
    at = now()
    business.tenant.created_at = at - timedelta(hours=2)
    system = "company_simulator:one"
    for i in range(205):
        source(
            session,
            business,
            system,
            "incoming",
            f"in-{i}",
            {
                "direction": "incoming",
                "message_id": f"m-{i}",
                "kind": "customer_email",
                "party_id": business.customer.id,
                "subject": f"Question {i}",
            },
            at - timedelta(minutes=50),
        )
    incoming = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == business.tenant.id,
            SourceRecord.external_id == "in-0",
        )
    )
    source(
        session, business, system, "ack", incoming.id, {}, at - timedelta(minutes=40)
    )
    for i in range(2):
        source(
            session,
            business,
            system,
            "outgoing",
            f"reply-{i}",
            {"direction": "outgoing", "in_reply_to": "m-0"},
            at - timedelta(minutes=20 - i),
        )
    source(
        session,
        business,
        "company_simulator:other",
        "outgoing",
        "wrong-run",
        {"direction": "outgoing", "in_reply_to": "m-1"},
        at - timedelta(minutes=10),
    )
    source(
        session,
        business,
        "mail-provider",
        "email_message",
        "external",
        {"direction": "inbound", "message": {"subject": "Imported provider message"}},
        at - timedelta(minutes=5),
    )
    foreign = core.create_tenant(session, "Foreign company")
    row = core.store_source_record(
        session,
        foreign.id,
        system,
        "outgoing",
        "foreign-reply",
        {"direction": "outgoing", "in_reply_to": "m-1"},
    )
    row = row[0]
    row.received_at = at - timedelta(minutes=5)
    session.flush()
    before = session.scalar(select(func.count()).select_from(SourceRecord))
    value = observe(session, business, at)
    mail = value["messages"]
    assert mail["unanswered"] == 204
    assert mail["unread"] == 204
    assert mail["customer_requests"] == 204
    assert mail["first_replies_last_hour"] == 1
    assert mail["external_incoming"] == 1
    assert mail["coverage"] == "partial"
    assert len(mail["evidence"]) == 4
    assert max(p["unanswered"] or 0 for p in mail["series"]) == 205
    assert mail["series"][-1]["unanswered"] == 204
    assert len(mail["series"]) == 13
    assert session.scalar(select(func.count()).select_from(SourceRecord)) == before


def test_supplier_work_and_returns_keep_partial_and_corrected_positions(
    session, business
):
    # BUSINESS PURPOSE: Received goods and physically disposed returns are different from closed documents or refunds.
    # BUSINESS RULE: Reuse canonical open promises and return disposition, excluding corrections and keeping partial work open.
    from test_returns import came_back, delivery, returns_area, stocked

    from reality.services.return_dispositions import record_return_disposition

    at = now()
    business.tenant.created_at = at - timedelta(hours=2)
    supplier = core.create_commitment(
        session,
        business.tenant.id,
        "supplier_delivery",
        business.supplier.id,
        business.company.id,
        business.item.id,
        business.location.id,
        "5",
        None,
    )
    receipt = core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "2",
        to_location_id=business.location.id,
        commitment_id=supplier.id,
        occurred_at=at - timedelta(minutes=10),
    )
    stocked(session, business)
    outgoing = delivery(session, business, 5)
    returned = came_back(
        session, business, outgoing, 5, returns_area(session, business)
    )
    record_return_disposition(
        session,
        business.tenant.id,
        returned.id,
        "restock",
        "2",
        destination_location_id=business.location.id,
    )
    value = observe(session, business, now())
    assert value["supply"]["open_lines"] == 1
    assert value["supply"]["unknown_due_lines"] == 1
    assert value["returns"]["arrived_positions"] == 1
    assert value["returns"]["resolved_positions"] == 0
    assert value["returns"]["pending_positions"] == 1
    record_return_disposition(
        session,
        business.tenant.id,
        returned.id,
        "restock",
        "3",
        destination_location_id=business.location.id,
    )
    assert observe(session, business, now())["returns"]["resolved_positions"] == 1
    core.correct_movement(
        session, business.tenant.id, receipt.id, reason="Receipt recorded in error"
    )
    assert observe(session, business, now())["supply"]["receipts_last_hour"] == 0
    core.record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "5",
        to_location_id=business.location.id,
        commitment_id=supplier.id,
        occurred_at=now(),
    )
    received = observe(session, business, now())["supply"]
    assert received["open_lines"] == 0
    assert received["fully_received_lines"] == 1
    assert received["evidence"][0]["id"] == supplier.id


def test_order_recording_deduplicates_and_unknown_mail_is_not_empty_success(
    session, business
):
    # BUSINESS PURPOSE: An idle empty queue is distinguishable from absent integration evidence.
    # BUSINESS RULE: Count one first-recorded order despite retries; unknown provider queue never becomes a green zero.
    at = now()
    business.tenant.created_at = at - timedelta(hours=2)
    document = core.create_document(
        session,
        business.tenant.id,
        "sales_order",
        "SO-flow",
        business.customer.id,
        "10",
    )
    core.emit_business_event(
        session, business.tenant.id, "document.recorded", "document", document.id, {}
    )
    session.flush()
    before = session.scalar(select(func.count()).select_from(BusinessEvent))
    value = observe(session, business, now())
    assert value["orders"]["received_last_hour"] == 1
    assert value["messages"]["coverage"] == "unavailable"
    assert value["messages"]["unanswered"] is None
    assert value["messages"]["signal"] == "unknown"
    assert session.scalar(select(func.count()).select_from(BusinessEvent)) == before


def test_stock_signal_uses_existing_oversold_rule_and_not_a_new_threshold(
    session, business
):
    # BUSINESS PURPOSE: Red stock risk must name actual uncovered customer demand.
    # BUSINESS RULE: The shared oversold evaluator retains its quantities/units and high severity.
    at = now()
    core.create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "10",
        at + timedelta(hours=4),
    )
    value = observe(session, business, now())
    assert value["stock"]["oversold_items"] == 1
    assert value["stock"]["signal"] == "critical"
    assert value["stock"]["exceptions"][0]["record_id"] == business.item.id
    assert value["stock"]["evaluated_classes"] == ["item_oversold"]
    assert value["orders"]["unlinked_open_lines"] == 1
    core.record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    assert observe(session, business, now())["stock"]["oversold_items"] == 0


def test_mail_future_evidence_and_company_creation_are_explicit_gaps(session, business):
    # BUSINESS PURPOSE: Future replies or periods before company creation cannot prove past queue progress.
    # BUSINESS RULE: Preserve unknown earlier graph points and do not answer until the recorded reply exists at observation time.
    at = now()
    business.tenant.created_at = at - timedelta(minutes=10)
    source(
        session,
        business,
        "company_simulator:clock",
        "incoming",
        "current",
        {"message_id": "message", "kind": "order"},
        at - timedelta(minutes=5),
    )
    source(
        session,
        business,
        "company_simulator:clock",
        "outgoing",
        "future",
        {"in_reply_to": "message"},
        at + timedelta(minutes=5),
    )
    value = observe(session, business, at)
    assert value["messages"]["unanswered"] == 1
    assert value["messages"]["first_replies_last_hour"] == 0
    assert value["messages"]["series"][0]["unanswered"] is None
    assert value["buckets"][0]["known"] is False
    assert value["messages"]["series"][-1]["unanswered"] == 1


def test_expanded_overview_shares_authorized_read_and_never_adopts_work(
    session, business, scheduled_owner, monkeypatch
):
    # BUSINESS PURPOSE: Web/CLI/MCP use one authorized observation, including its complete operating flows.
    # BUSINESS RULE: Existing company membership and read-only feature guards protect the additive DTO without adopting cases.
    import pytest

    from reality.services import operations_cockpit
    from reality.services.memberships import Principal

    monkeypatch.setenv("REALITY_OPERATIONS_COCKPIT_ENABLED", "true")
    session.commit()
    value = operations_cockpit.operations_cockpit(
        session, business.tenant.id, Principal(scheduled_owner.id)
    )
    assert value["flows"]["orders"]["open_orders"] == 0
    assert value["supported_cases"]["adopted"] is False
    with pytest.raises(core.NotFound):
        operations_cockpit.operations_cockpit(
            session, business.tenant.id, Principal("unrelated-user")
        )


def test_supplier_totals_are_complete_beyond_the_evidence_preview(session, business):
    # BUSINESS PURPOSE: A handful of preview rows must not hide the full supply queue.
    # BUSINESS RULE: Every active open supplier line counts, including partial lines; completed receipts remain distinct.
    at = now()
    for i in range(7):
        core.create_commitment(
            session,
            business.tenant.id,
            "supplier_delivery",
            business.supplier.id,
            business.company.id,
            business.item.id,
            business.location.id,
            "3",
            at + timedelta(days=2),
        )
    value = observe(session, business, now())
    assert value["supply"]["open_lines"] == 7
    assert len(value["supply"]["evidence"]) == 4
    assert value["supply"]["signal"] == "progress"
