"""Spec 296: an order with an unknown SKU keeps its known lines; a person assigns the rest."""

import json

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import (
    BusinessEvent,
    Commitment,
    DocumentLine,
    ImportJob,
)
from reality.services import core
from reality.services.delivery_actions import prepare_delivery_action
from reality.services.exceptions import operational_exceptions
from reality.services.order_line_items import assign_line_item, preview_item_assignment
from reality.tools.application import approve_and_execute_proposal

ORDER = 8101


def _payload(**changes):
    return {
        "id": ORDER,
        "name": f"#{ORDER}",
        "currency": "EUR",
        "total_price": "70.00",
        "created_at": "2026-09-01T10:00:00Z",
        "updated_at": "2026-09-01T10:00:00Z",
        "line_items": [
            {"id": 81, "sku": "BIKE-LIGHT", "quantity": 2, "price": "10.00"},
            {
                "id": 82,
                "sku": "HELMET-M",
                "name": "Helmet M",
                "quantity": 5,
                "price": "10.00",
            },
        ],
        **changes,
    }


def _intake(session, business, payload):
    source, job = core.enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    return source, job, core.process_import_job(session, business.tenant.id, job.id)


def _unknown_line(session, business):
    return session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == business.tenant.id,
            DocumentLine.sku == "HELMET-M",
        )
    ).one()


def _findings(session, business):
    return [
        row
        for row in operational_exceptions(session, business.tenant.id)
        if row.class_id == "order_line_item_unknown"
    ]


def _helmet(session, business):
    return core.create_item(session, business.tenant.id, "HELMET-M-01", "Helmet M")


def test_known_lines_are_interpreted_and_the_unknown_one_is_kept(session, business):
    _, job, result = _intake(session, business, _payload())

    assert session.get(ImportJob, (business.tenant.id, job.id)).status == "completed"
    _, order, lines, commitments = result
    assert len(lines) == 2
    assert [commitment.item_id for commitment in commitments] == [business.item.id]
    unknown = _unknown_line(session, business)
    assert unknown.item_id is None and unknown.document_id == order.id
    assert (unknown.quantity, unknown.description) == (5, "Helmet M")
    assert (
        session.scalar(
            select(func.count())
            .select_from(Commitment)
            .where(Commitment.document_line_id == unknown.id)
        )
        == 0
    )


def test_an_unknown_item_line_is_reported_until_an_item_is_assigned(session, business):
    # Positive control for the absence: an order of known items reports nothing.
    _intake(
        session,
        business,
        {**_payload(id=8100, name="#8100"), "line_items": _payload()["line_items"][:1]},
    )
    assert _findings(session, business) == []

    _intake(session, business, _payload())
    (finding,) = _findings(session, business)
    unknown = _unknown_line(session, business)
    assert finding.record_id == unknown.id
    assert finding.causal_values["sku"] == "HELMET-M"
    assert finding.trace["document_id"] == unknown.document_id

    assign_line_item(
        session,
        business.tenant.id,
        document_line_id=unknown.id,
        item_id=_helmet(session, business).id,
    )

    assert _findings(session, business) == []


def test_assigning_an_item_creates_the_promise_from_the_order(session, business):
    _intake(session, business, _payload())
    unknown = _unknown_line(session, business)
    helmet = _helmet(session, business)

    preview = preview_item_assignment(
        session, business.tenant.id, document_line_id=unknown.id, item_id=helmet.id
    )
    assert preview["location_id"] == business.location.id
    assert preview["from_party_id"] == business.company.id

    result = assign_line_item(
        session, business.tenant.id, document_line_id=unknown.id, item_id=helmet.id
    )

    promise = record_by_id(session, Commitment, result["commitment_id"])
    assert (promise.item_id, promise.quantity, promise.to_party_id) == (
        helmet.id,
        5,
        business.customer.id,
    )
    assert promise.document_line_id == unknown.id
    assert record_by_id(session, DocumentLine, unknown.id).item_id == helmet.id
    event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.event_type == "document_line.item_assigned",
            BusinessEvent.subject_id == unknown.id,
        )
    ).one()
    assert json.loads(event.payload)["commitment_id"] == promise.id


def test_the_reviewed_assignment_confirms_through_the_delivery_review(
    session, business
):
    _intake(session, business, _payload())
    unknown = _unknown_line(session, business)
    helmet = _helmet(session, business)

    proposal = prepare_delivery_action(
        session,
        business.tenant.id,
        "order_line_item_assign",
        {"document_line_id": unknown.id, "item_id": helmet.id},
        request_id="assign-helmet",
    )
    review = json.loads(proposal.input)["_delivery_review"]
    assert review["effect"]["money_moves"] is False
    assert record_by_id(session, DocumentLine, unknown.id).item_id is None

    executed = approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        review_token=review["token"],
        confirmed=True,
    )

    assert executed.status == "executed"
    assert record_by_id(session, DocumentLine, unknown.id).item_id == helmet.id


@pytest.mark.parametrize(
    ("case", "code"),
    [
        ("assigned", "order_line_item_already_assigned"),
        ("not_item_line", "order_line_item_not_item_line"),
        ("not_sales_order", "order_line_item_assign_not_sales_order"),
        ("closed", "order_line_item_order_closed"),
    ],
)
def test_an_assignment_names_why_it_is_refused(session, business, case, code):
    tenant = business.tenant.id
    _, _, result = _intake(session, business, _payload())
    unknown = _unknown_line(session, business)
    helmet = _helmet(session, business)
    line_id = unknown.id
    if case == "assigned":
        assign_line_item(
            session, tenant, document_line_id=unknown.id, item_id=helmet.id
        )
    elif case == "not_item_line":
        unknown.line_type = "shipping"
        session.commit()
    elif case == "not_sales_order":
        purchase = core.create_document(
            session, tenant, "purchase_order", "PO-8101", business.supplier.id, "10"
        )
        line = DocumentLine(
            id=core.uid("lin"),
            tenant_id=tenant,
            document_id=purchase.id,
            sku="HELMET-M",
            quantity=1,
            unit_price=10,
            gross_amount=10,
            line_type="item",
        )
        session.add(line)
        session.commit()
        line_id = line.id
    elif case == "closed":
        for commitment in result[3]:
            core.cancel_commitment(session, tenant, commitment.id, reason="Test")

    with pytest.raises(core.InvalidOperation) as refused:
        assign_line_item(session, tenant, document_line_id=line_id, item_id=helmet.id)
    assert refused.value.code == code


def test_a_cancelled_order_no_longer_reports_its_unknown_line(session, business):
    _, _, result = _intake(session, business, _payload())
    assert _findings(session, business)

    for commitment in result[3]:
        core.cancel_commitment(
            session, business.tenant.id, commitment.id, reason="Test"
        )

    assert _findings(session, business) == []


def test_the_unknown_line_stays_in_its_company(session, business):
    _intake(session, business, _payload())
    unknown = _unknown_line(session, business)
    other = core.create_tenant(session, "Other GmbH")

    with pytest.raises(core.NotFound):
        preview_item_assignment(
            session, other.id, document_line_id=unknown.id, item_id=business.item.id
        )


def test_a_cancelled_order_of_unknown_items_alone_is_not_reported(session, business):
    only_unknown = _payload(
        id=8102,
        name="#8102",
        line_items=[{"id": 83, "sku": "HELMET-M", "quantity": 1, "price": "10.00"}],
    )
    _intake(session, business, only_unknown)
    assert _findings(session, business)

    _intake(
        session,
        business,
        {
            **only_unknown,
            "updated_at": "2026-09-02T10:00:00Z",
            "cancelled_at": "2026-09-02T10:00:00Z",
        },
    )

    assert _findings(session, business) == []
    line = _unknown_line(session, business)
    with pytest.raises(core.InvalidOperation) as refused:
        preview_item_assignment(
            session,
            business.tenant.id,
            document_line_id=line.id,
            item_id=_helmet(session, business).id,
        )
    assert refused.value.code == "order_line_item_order_closed"


def test_empty_and_null_skus_are_reported_and_non_shipping_lines_are_kept(
    session, business
):
    _intake(
        session,
        business,
        _payload(
            line_items=[
                {
                    "id": 84,
                    "sku": None,
                    "name": "Engraving plate",
                    "quantity": 1,
                    "price": "5.00",
                },
                {
                    "id": 85,
                    "sku": "",
                    "name": "Custom frame",
                    "quantity": 1,
                    "price": "50.00",
                },
                {
                    "id": 86,
                    "sku": "",
                    "name": "Tip",
                    "quantity": 1,
                    "price": "2.00",
                    "requires_shipping": False,
                },
            ]
        ),
    )

    lines = {
        line.source_line_id: line
        for line in session.scalars(
            select(DocumentLine).where(DocumentLine.tenant_id == business.tenant.id)
        )
    }
    assert lines["84"].sku == "" and lines["86"].line_type == "service"
    reported = {finding.record_id for finding in _findings(session, business)}
    assert reported == {lines["84"].id, lines["85"].id}


def test_an_inactive_item_cannot_be_assigned_and_the_unit_follows_the_item(
    session, business
):
    _intake(session, business, _payload())
    unknown = _unknown_line(session, business)
    helmet = core.create_item(
        session, business.tenant.id, "HELMET-BOX", "Helmet box", unit="box"
    )
    helmet.is_active = False
    session.commit()

    with pytest.raises(core.InvalidOperation) as refused:
        preview_item_assignment(
            session, business.tenant.id, document_line_id=unknown.id, item_id=helmet.id
        )
    assert refused.value.code == "order_line_item_item_inactive"

    helmet.is_active = True
    session.commit()
    assign_line_item(
        session, business.tenant.id, document_line_id=unknown.id, item_id=helmet.id
    )
    assert record_by_id(session, DocumentLine, unknown.id).unit == "box"
