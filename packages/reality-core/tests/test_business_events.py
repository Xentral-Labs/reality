import json
from datetime import timedelta

from sqlalchemy import select

from reality.db.core import BusinessEvent, Document, now
from reality.services.core import (
    activity_signal,
    business_events,
    create_commitment,
    create_item,
    create_tenant,
    emit_business_event,
    record_movement,
    reserve,
    store_source_record,
    timeline_activity,
)


def test_business_history_areas_counts_and_tenant_boundary(session, business):
    other = create_tenant(session, "Other history company")
    for identifier, tenant_id, kind in (
        ("doc_history_sale", business.tenant.id, "sales_order"),
        ("doc_history_purchase", business.tenant.id, "purchase_order"),
        ("doc_history_foreign", other.id, "sales_order"),
    ):
        session.add(
            Document(id=identifier, tenant_id=tenant_id, type=kind, number=identifier)
        )
        session.flush()
        emit_business_event(
            session,
            tenant_id,
            "document.recorded",
            "document",
            identifier,
            {"type": kind, "number": identifier},
        )
    session.flush()
    sales = timeline_activity(
        session, business.tenant.id, area="sales", hours=0, limit=1
    )
    assert [row["subject_id"] for row in sales["events"]] == ["doc_history_sale"]
    assert not sales["has_more"]
    purchasing = timeline_activity(
        session, business.tenant.id, area="purchasing", hours=0
    )
    assert [row["subject_id"] for row in purchasing["events"]] == [
        "doc_history_purchase"
    ]
    assert (
        sales["business_counts"]
        == purchasing["business_counts"]
        == {
            "sales_orders": 1,
            "purchase_orders": 1,
            "deliveries": 0,
            "invoices": 0,
        }
    )


def test_history_search_cursor_and_record_counts(session, business):
    for index in range(3):
        emit_business_event(
            session,
            business.tenant.id,
            "movement.recorded",
            "movement",
            f"mov_history_{index}",
            {"item_id": business.item.id},
            occurred_at=now() - timedelta(days=45),
        )
    session.flush()
    first = timeline_activity(
        session,
        business.tenant.id,
        hours=0,
        query=business.item.name,
        record_type="movement",
        limit=2,
    )
    assert len(first["events"]) == 2
    assert first["has_more"]
    second = timeline_activity(
        session,
        business.tenant.id,
        hours=0,
        query=business.item.name,
        record_type="movement",
        limit=2,
        before_sequence=first["events"][-1]["sequence"],
    )
    assert len(second["events"]) == 1
    assert not {row["id"] for row in first["events"]} & {
        row["id"] for row in second["events"]
    }
    assert first["record_counts"] == second["record_counts"]
    assert first["record_counts"]["movement"] == 0  # Events are not stored movements.
    assert first["business_counts"]["deliveries"] == 0
    assert first["events"][0]["business_context"]["item"] == business.item.name
    assert (
        len(
            timeline_activity(session, business.tenant.id, hours=0, area="warehouse")[
                "events"
            ]
        )
        == 3
    )
    assert not timeline_activity(
        session, business.tenant.id, hours=24, record_type="movement"
    )["events"]


def test_activity_signal_uses_tenant_sequence_cursor(session, business):
    baseline = activity_signal(session, business.tenant.id, after_sequence=0)
    emit_business_event(
        session,
        business.tenant.id,
        "source_record.received",
        "source_record",
        "src_live",
        {},
    )
    emit_business_event(
        session,
        business.tenant.id,
        "document.rejected",
        "document",
        "doc_live",
        {},
    )
    session.flush()

    signal = activity_signal(
        session, business.tenant.id, after_sequence=baseline["latest_sequence"]
    )

    assert signal == {
        "latest_sequence": baseline["latest_sequence"] + 2,
        "new_events": 2,
        "attention_events": 1,
    }


def test_timeline_activity_leads_with_business_context_and_retains_trace(
    session, business
):
    source, _, _ = store_source_record(
        session,
        business.tenant.id,
        "shopify",
        "order",
        "ORDER-1048",
        {"id": "ORDER-1048"},
    )
    emit_business_event(
        session,
        business.tenant.id,
        "document.recorded",
        "document",
        "doc_1048",
        {
            "type": "sales_order",
            "number": "1048",
            "party_id": business.customer.id,
            "amount": "199.90",
            "currency": "EUR",
        },
        source_record_id=source.id,
        correlation_id=source.id,
    )
    emit_business_event(
        session,
        business.tenant.id,
        "commitment.created",
        "commitment",
        "com_1048",
        {
            "type": "customer_delivery",
            "item_id": business.item.id,
            "quantity": "2",
            "document_id": "doc_1048",
        },
        source_record_id=source.id,
        correlation_id=source.id,
    )
    session.flush()

    activity = timeline_activity(session, business.tenant.id)["activities"][0]

    assert activity["business_title"] == "Sales order 1048 processed"
    assert "Shopify" in activity["business_detail"]
    assert business.customer.name in activity["business_detail"]
    assert any(
        event["business_title"] == "Delivery commitment created"
        and business.item.name in event["business_detail"]
        and "2" in event["business_detail"]
        for event in activity["events"]
    )
    assert {event["subject_id"] for event in activity["events"]} >= {
        "doc_1048",
        "com_1048",
    }


def test_domain_changes_emit_ordered_tenant_scoped_events(session, business):
    commitment = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        2,
        "2026-09-05",
    )
    record_movement(
        session,
        business.tenant.id,
        "opening_stock",
        business.item.id,
        2,
        to_location_id=business.location.id,
    )
    reservation = reserve(session, business.tenant.id, commitment.id)

    events = business_events(session, business.tenant.id)
    assert [event.sequence for event in events] == list(range(1, len(events) + 1))
    assert events[-1].event_type == "reservation.created"
    assert events[-1].subject_id == reservation.reservation.id
    assert json.loads(events[-1].payload)["commitment_id"] == commitment.id
    assert all(event.tenant_id == business.tenant.id for event in events)


def test_business_event_rolls_back_with_business_transaction(session, business):
    item = create_item(session, business.tenant.id, "ROLLBACK", "Rollback item")
    before = len(business_events(session, business.tenant.id))
    item.name = "Uncommitted"
    emit_business_event(
        session,
        business.tenant.id,
        "item.updated",
        "item",
        item.id,
        {"name": item.name},
    )
    session.rollback()

    assert len(business_events(session, business.tenant.id)) == before
    assert (
        session.scalar(
            select(BusinessEvent).where(BusinessEvent.subject_id == item.id)
        ).event_type
        == "item.created"
    )
