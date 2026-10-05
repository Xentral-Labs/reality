from test_fulfillment_readiness import _prepayment_order
from test_mcp_read_contract import order

from reality.mcp.catalog import dispatch_tool
from reality.services.core import create_commitment
from reality.services.fulfillment_readiness import fulfillment_readiness
from reality.services.projections import (
    FULFILLMENT_QUEUE,
    projection_rows,
    refresh_projection,
)


def test_standard_basis_and_read_parity(session, business):
    _, document, _, commitments = order(session, business)
    promise = next(c for c in commitments if c.type == "customer_delivery")
    ready = dispatch_tool(
        session,
        business.tenant.id,
        "fulfillment_readiness",
        {"commitment_id": promise.id},
    )
    meaning = ready["payment_interpretation"]
    assert meaning["amount_basis"] == {
        "kind": "stated_order_gross",
        "amount": ready["required_amount"],
        "currency": ready["currency"],
        "document_id": document.id,
    }
    assert meaning["payment_evidence"]["status"] == "not_evaluated"
    assert meaning["payment_evidence"]["received"] is None
    assert meaning["payment_evidence"]["remaining"] is None
    assert meaning["shipment_constraint"]["status"] == "not_required"
    assert "not an unpaid invoice" in meaning["notice"]
    explained = dispatch_tool(
        session, business.tenant.id, "order_explain", {"order_reference": document.id}
    )
    assert (
        explained["fulfillment"]["lines"][0]["readiness"]["payment_interpretation"]
        == meaning
    )
    assert "payment_interpretation" not in fulfillment_readiness(
        session, business.tenant.id, promise.id
    ).as_dict(include_interpretation=False)
    from sqlalchemy import select

    from reality.db.core import ProjectionRow

    assert all(
        "payment_interpretation" not in p
        for p in session.scalars(
            select(ProjectionRow.payload).where(
                ProjectionRow.tenant_id == business.tenant.id
            )
        )
    )


def test_orphan_zero_is_not_stated(session, business):
    promise = create_commitment(
        session,
        business.tenant.id,
        "customer_delivery",
        business.company.id,
        business.customer.id,
        business.item.id,
        business.location.id,
        "1",
        None,
    )
    ready = fulfillment_readiness(session, business.tenant.id, promise.id).as_dict()
    assert ready["required_amount"] == "0"
    assert ready["payment_interpretation"]["amount_basis"]["kind"] == "not_established"
    assert ready["payment_interpretation"]["amount_basis"]["amount"] is None


def test_unstated_prepayment_is_unknown(session, business):
    document, _, promise = _prepayment_order(session, business)
    document.gross_amount = None
    session.flush()
    meaning = fulfillment_readiness(session, business.tenant.id, promise.id).as_dict()[
        "payment_interpretation"
    ]
    assert meaning["amount_basis"]["kind"] == "unstated"
    assert meaning["payment_evidence"]["status"] == "amount_unstated"
    assert meaning["payment_evidence"]["received"] is None
    assert meaning["payment_evidence"]["remaining"] is None
    assert meaning["shipment_constraint"]["blocker_codes"] == [
        "prepayment_amount_unstated"
    ]
    assert meaning["shipment_constraint"]["status"] == "blocked"


def test_existing_queue_payment_readiness_shares_interpretation(session, business):
    _, _, promise = _prepayment_order(session, business)
    ready = fulfillment_readiness(session, business.tenant.id, promise.id).as_dict()
    meaning = ready["payment_interpretation"]
    fresh = dispatch_tool(session, business.tenant.id, "fulfillment_queue", {})
    assert (
        fresh["records"][0]["lines"][0]["fulfillment_readiness"][
            "payment_interpretation"
        ]
        == meaning
    )
    refresh_projection(session, business.tenant.id, projection_name=FULFILLMENT_QUEUE)
    assert (
        projection_rows(session, business.tenant.id, FULFILLMENT_QUEUE)[0]["lines"][0][
            "fulfillment_readiness"
        ]["payment_interpretation"]
        == meaning
    )
    from sqlalchemy import select

    from reality.db.core import ProjectionRow

    assert all(
        "payment_interpretation" not in p
        for p in session.scalars(
            select(ProjectionRow.payload).where(
                ProjectionRow.tenant_id == business.tenant.id
            )
        )
    )
