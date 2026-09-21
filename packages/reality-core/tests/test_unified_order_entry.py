"""One reviewed agreement produces exact traceable deliveries, never duplicate effects."""

import json
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import (
    BusinessEvent,
    Commitment,
    Document,
    DocumentLine,
    LedgerEntry,
    Movement,
    Reservation,
    SourceRecord,
)
from reality.services.core import (
    InvalidOperation,
    NotFound,
    create_tenant,
    record_movement,
    reserve,
    update_item,
)
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.tools.application import approve_and_execute_proposal


def intent(business, direction="sales"):
    return {
        "direction": direction,
        "number": "ORDER-119",
        "company_party_id": business.company.id,
        "counterparty_id": business.customer.id
        if direction == "sales"
        else business.supplier.id,
        "location_id": business.location.id,
        "currency": "EUR",
        "gross_amount": "98.73",
        "customer_reference": "Exact <customer> note",
        "requested_delivery_at": "2026-10-10T10:00:00Z",
        "lines": [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "12.50",
                "gross_amount": "24.91",
            },
            {
                "item_id": business.item.id,
                "quantity": "3",
                "unit_price": "12.50",
                "gross_amount": "37.11",
                "description": "Second line",
                "external_note": "Retained <source> metadata",
            },
        ],
    }


def prepare(session, business, values=None, request="order-119"):
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "order_create",
        values or intent(business),
        request_id=request,
    )


def confirm(session, business, proposal):
    return approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=json.loads(proposal.input)["_delivery_review"]["token"],
        confirmed=True,
    )


@pytest.mark.parametrize("direction", ["sales", "purchase"])
def test_multiline_review_trace_and_replay(session, business, direction):
    values = intent(business, direction)
    proposal = prepare(session, business, values)
    for model in (Document, Movement, Reservation, LedgerEntry):
        assert (
            session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.tenant_id == business.tenant.id)
            )
            == 0
        )
    with pytest.raises(InvalidOperation, match="confirmation"):
        approve_and_execute_proposal(session, business.tenant.id, proposal.id)
    confirm(session, business, proposal)
    result = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert result["verification"] == "verified"
    receipt = result["receipt"]
    source = record_by_id(session, SourceRecord, receipt["source_record_id"])
    assert json.loads(source.payload)["gross_amount"] == "98.73"
    assert (
        json.loads(source.payload)["lines"][1]["external_note"]
        == "Retained <source> metadata"
    )
    doc = record_by_id(session, Document, receipt["document_id"])
    assert doc.gross_amount == Decimal("98.73")
    assert doc.source_record_id == source.id
    assert len(receipt["commitment_ids"]) == 2
    for index, cid in enumerate(receipt["commitment_ids"]):
        commitment = record_by_id(session, Commitment, cid)
        line = record_by_id(session, DocumentLine, receipt["document_line_ids"][index])
        assert commitment.document_line_id == line.id
        assert commitment.type == (
            "customer_delivery" if direction == "sales" else "supplier_delivery"
        )
        assert commitment.amount == Decimal(values["lines"][index]["gross_amount"])
    confirm(session, business, proposal)
    assert json.loads(proposal.output) == receipt
    assert (
        session.scalar(
            select(func.count())
            .select_from(Movement)
            .where(Movement.tenant_id == business.tenant.id)
        )
        == 0
    )
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == business.tenant.id)
        )
        == 1
    )


@pytest.mark.parametrize(
    "change", ["total", "line_total", "foreign", "empty", "date", "quantity", "extra"]
)
def test_invalid_order_is_rejected_before_evidence(session, business, change):
    values = intent(business)
    if change == "total":
        values.pop("gross_amount")
    elif change == "line_total":
        values["lines"][1].pop("gross_amount")
    elif change == "foreign":
        values["lines"][1]["item_id"] = "foreign"
    elif change == "empty":
        values["lines"] = []
    elif change == "date":
        values["requested_delivery_at"] = "wrong"
    elif change == "quantity":
        values["lines"][1]["quantity"] = "-1"
    else:
        values["unsupported"] = True
    with pytest.raises((InvalidOperation, NotFound)):
        prepare(session, business, values)
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == business.tenant.id)
        )
        == 0
    )


def test_stale_reference_and_unknown_recovery(session, business):
    proposal = prepare(session, business)
    item = business.item
    update_item(
        session, business.tenant.id, item.id, item.sku, "Renamed item", item.unit
    )
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, business, proposal)
    next_proposal = prepare(session, business, request="fresh")
    confirm(session, business, next_proposal)
    receipt = json.loads(next_proposal.output)
    next_proposal.status = "executing"
    next_proposal.output = "{}"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        candidate = prepare(session, business, request="duplicate")
        confirm(session, business, candidate)
    result = reconcile_delivery(session, business.tenant.id, next_proposal.id)
    assert result["receipt"] == receipt
    assert result["verification"] == "verified"
    other = create_tenant(session, "Foreign")
    with pytest.raises(NotFound):
        delivery_proposal_detail(session, other.id, next_proposal.id)


def test_historical_proof_after_partial_delivery_and_receipt_mismatch(
    session, business
):
    proposal = prepare(session, business)
    confirm(session, business, proposal)
    receipt = json.loads(proposal.output)
    record_movement(
        session,
        business.tenant.id,
        "receipt",
        business.item.id,
        "5",
        to_location_id=business.location.id,
    )
    reserve(session, business.tenant.id, receipt["commitment_ids"][0], "1")
    record_movement(
        session,
        business.tenant.id,
        "shipment",
        business.item.id,
        "1",
        from_location_id=business.location.id,
        commitment_id=receipt["commitment_ids"][0],
    )
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    assert Decimal(detail["observation"]["deliveries"][0]["open"]) == 1
    proposal.output = json.dumps({**receipt, "document_id": "different"})
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_same_number_distinct_agreements_and_exact_duplicate_rejection(
    session, business
):
    first = prepare(session, business)
    confirm(session, business, first)
    first_receipt = json.loads(first.output)
    with pytest.raises(InvalidOperation, match="already recorded"):
        prepare(session, business, request="exact-duplicate")
    changed = intent(business)
    changed["customer_reference"] = "Different agreement"
    second = prepare(session, business, changed, request="legitimate-second")
    confirm(session, business, second)
    second_receipt = json.loads(second.output)
    assert first_receipt["document_id"] != second_receipt["document_id"]
    assert first_receipt["source_record_id"] != second_receipt["source_record_id"]
    assert (
        delivery_proposal_detail(session, business.tenant.id, first.id)["verification"]
        == "verified"
    )
    assert (
        delivery_proposal_detail(session, business.tenant.id, second.id)["verification"]
        == "verified"
    )


def test_missing_or_ambiguous_evidence_is_not_success(session, business):
    proposal = prepare(session, business)
    confirm(session, business, proposal)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "order.recorded",
        )
    )
    event.action_id = None
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_order_http_authorization_and_practice_boundary(session, business):
    from types import SimpleNamespace

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import Tenant
    from reality.services.core import uid
    from reality.web.api import database_session
    from reality.web.app import app

    proposal = prepare(session, business)
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)["_delivery_review"]["token"],
            confirming_principal=SimpleNamespace(
                user_id="absent", is_platform_admin=False
            ),
        )
    factory = sessionmaker(session.bind, expire_on_commit=False)

    def database():
        with factory() as connection:
            yield connection

    app.dependency_overrides[database_session] = database
    try:
        with TestClient(app) as client:
            base = f"/api/tenants/{business.tenant.id}"
            response = client.post(
                f"{base}/delivery-actions/prepare",
                json={
                    "tool": "order_create",
                    "request_id": "http",
                    "arguments": intent(business, "purchase"),
                },
            )
            assert response.status_code == 200, response.text
            value = response.json()
            result = client.post(
                f"{base}/change-proposals/{value['id']}/approve",
                json={"confirmed": True, "review_token": value["review"]["token"]},
            )
            assert result.status_code == 200, result.text
            assert (
                client.get(f"{base}/delivery-actions/{value['id']}").json()[
                    "verification"
                ]
                == "verified"
            )
    finally:
        app.dependency_overrides.clear()
    practice = Tenant(id=uid("ten"), name="Practice", purpose="playground")
    session.add(practice)
    session.commit()
    with pytest.raises(InvalidOperation, match="practice"):
        prepare_delivery_action(
            session,
            practice.id,
            "order_create",
            intent(business),
            request_id="practice",
        )


def test_two_prepared_orders_cannot_record_the_same_payload(session, business):
    first = prepare(session, business, request="first")
    second = prepare(session, business, request="second")
    confirm(session, business, first)
    with pytest.raises(InvalidOperation, match="already recorded"):
        confirm(session, business, second)
    assert second.status == "proposed"
    assert (
        session.scalar(
            select(func.count())
            .select_from(Document)
            .where(Document.tenant_id == business.tenant.id)
        )
        == 1
    )


def test_creation_snapshot_must_prove_directed_commitments(session, business):
    proposal = prepare(session, business)
    confirm(session, business, proposal)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "order.recorded",
        )
    )
    payload = json.loads(event.payload)
    payload["commitments"][0]["to_party_id"] = business.company.id
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )
