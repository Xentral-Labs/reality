"""A journey follows order-owned reality, never shared business references."""

import pytest
from fastapi.testclient import TestClient

from reality.db.core import BusinessEvent, DocumentLine, now
from reality.services.core import (
    NotFound,
    create_commitment,
    create_document,
    create_tenant,
    emit_business_event,
    observe_fact,
    post_ledger,
    record_movement,
    reserve,
    store_source_record,
)
from reality.services.order_journey import order_journey, search_order_journeys


def order(session, business, number):
    tenant = business.tenant.id
    source, _, _ = store_source_record(
        session, tenant, "shop", "order", number, {"number": number}
    )
    document = create_document(
        session,
        tenant,
        "sales_order",
        number,
        business.customer.id,
        "100",
        source_record_id=source.id,
    )
    line = DocumentLine(
        id=f"line-{number}",
        tenant_id=tenant,
        document_id=document.id,
        sku=business.item.sku,
        item_id=business.item.id,
        quantity=3,
    )
    session.add(line)
    session.flush()
    commitment = create_commitment(
        session,
        tenant,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "3",
        None,
        document_line_id=line.id,
    )
    return document, commitment, source


def test_journey_uses_shortest_links_and_does_not_merge_shared_references(
    session, business
):
    tenant = business.tenant.id
    first, commitment, source = order(session, business, "SO-1")
    second, unrelated, _ = order(session, business, "SO-2")
    record_movement(
        session,
        tenant,
        "receipt",
        business.item.id,
        "10",
        to_location_id=business.location.id,
    )
    reservation = reserve(session, tenant, commitment.id).reservation
    movement = record_movement(
        session,
        tenant,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=commitment.id,
    )
    fact = observe_fact(
        session,
        tenant,
        source_record_id=source.id,
        subject_type="commitment",
        subject_id=commitment.id,
        predicate="order.delivery_instruction",
        value="Fragile",
        observed_at=now(),
        idempotency_key="order-fact",
    )
    observe_fact(
        session,
        tenant,
        source_record_id=source.id,
        subject_type="commitment",
        subject_id=unrelated.id,
        predicate="order.delivery_instruction",
        value="Shared",
        observed_at=now(),
        idempotency_key="item-fact",
    )
    result = order_journey(session, tenant, first.id)
    subjects = {e["subject_id"] for e in result["events"]}
    assert {first.id, commitment.id, reservation.id, movement.id, fact.id} <= subjects
    assert second.id not in subjects and unrelated.id not in subjects
    assert not any(e["payload"].get("value") == "Shared" for e in result["events"])
    edge_pairs = {(e["from"]["id"], e["to"]["id"]) for e in result["edges"]}
    assert (commitment.id, reservation.id) in edge_pairs
    assert (commitment.id, movement.id) in edge_pairs
    assert (first.id, reservation.id) not in edge_pairs
    assert (commitment.id, fact.id) in edge_pairs
    assert result["order"]["number"] == "SO-1"


def test_journey_filters_before_pagination_and_preserves_repeated_changes(
    session, business
):
    tenant = business.tenant.id
    document, commitment, _ = order(session, business, "PAGED")
    baseline = order_journey(session, tenant, document.id)
    marker = max(e["sequence"] for e in baseline["events"])
    for index in range(5):
        emit_business_event(
            session,
            tenant,
            "commitment.changed",
            "commitment",
            commitment.id,
            {"revision": index},
        )
        emit_business_event(
            session, tenant, "item.updated", "item", business.item.id, {}
        )
    session.flush()
    first = order_journey(session, tenant, document.id, limit=2)
    assert len(first["events"]) == 2 and first["has_more"]
    assert all(e["subject_id"] == commitment.id for e in first["events"])
    second = order_journey(
        session,
        tenant,
        document.id,
        limit=2,
        before_sequence=first["events"][-1]["sequence"],
    )
    assert not {e["id"] for e in first["events"]} & {e["id"] for e in second["events"]}
    forward = order_journey(
        session, tenant, document.id, after_sequence=marker, limit=2
    )
    assert forward["has_more"]
    assert [e["payload"]["revision"] for e in forward["events"]] == [0, 1]


def test_journey_search_and_tenant_boundaries(session, business):
    document, _, _ = order(session, business, "SO-SEARCH")
    other = create_tenant(session, "Foreign")
    with pytest.raises(NotFound):
        order_journey(session, other.id, document.id)
    purchase = create_document(
        session, business.tenant.id, "purchase_order", "PO", business.supplier.id, "1"
    )
    with pytest.raises(NotFound):
        order_journey(session, business.tenant.id, purchase.id)
    assert not search_order_journeys(session, other.id)["orders"]
    assert [
        r["id"]
        for r in search_order_journeys(session, business.tenant.id, query="SEARCH")[
            "orders"
        ]
    ] == [document.id]
    assert search_order_journeys(
        session, business.tenant.id, query=business.customer.name
    )["orders"]


def test_journey_http_and_no_fabricated_events(session, business):
    from reality.web.api import database_session
    from reality.web.app import app

    document, _, _ = order(session, business, "API")
    app.dependency_overrides[database_session] = lambda: session
    try:
        with TestClient(app) as client:
            assert client.get("/api/tenants/missing/order-journeys").status_code == 404
            path = f"/api/tenants/{business.tenant.id}/order-journeys"
            assert client.get(path).json()["orders"][0]["id"] == document.id
            result = client.get(f"{path}/{document.id}?limit=1")
            assert result.status_code == 200
            assert len(result.json()["events"]) == 1
            assert client.get(f"{path}/missing").status_code == 404
            assert client.get(f"{path}/{document.id}?limit=251").status_code == 422
            assert (
                client.get(
                    f"{path}/{document.id}?before_sequence=3&after_sequence=1"
                ).status_code
                == 400
            )
        # A held document without recorded events must not invent a timeline date.
        from sqlalchemy import delete

        session.execute(
            delete(BusinessEvent).where(BusinessEvent.tenant_id == business.tenant.id)
        )
        assert not order_journey(session, business.tenant.id, document.id)["events"]
    finally:
        app.dependency_overrides.clear()


def test_posting_group_events_keep_ledger_entry_identity(session, business):
    document, _, _ = order(session, business, "POSTED")
    entries = post_ledger(
        session,
        business.tenant.id,
        document.id,
        business.customer.id,
        [("accounts_receivable", "debit", "100"), ("sales_revenue", "credit", "100")],
    )
    result = order_journey(session, business.tenant.id, document.id)
    event = next(e for e in result["events"] if e["type"] == "ledger.posted")
    assert event["subject_type"] == "posting_group"
    assert event["subject_id"] == entries[0].posting_group_id
    assert {
        edge["to"]["id"]
        for edge in result["edges"]
        if edge["from"]["kind"] == "posting_group"
    } == {entry.id for entry in entries}


def test_posting_entry_links_are_bounded_and_report_truncation(session, business):
    document, _, _ = order(session, business, "MANY-POSTINGS")
    post_ledger(
        session,
        business.tenant.id,
        document.id,
        business.customer.id,
        [("accounts_receivable", "debit", "1"), ("sales_revenue", "credit", "1")] * 126,
    )
    result = order_journey(session, business.tenant.id, document.id)
    assert result["links_truncated"]
    assert (
        len(
            [
                edge
                for edge in result["edges"]
                if edge["from"]["kind"] == "posting_group"
            ]
        )
        == 250
    )
