"""Reviewed invoice entry preserves stated evidence and avoids duplicate effects."""

import json
from decimal import Decimal

import pytest
from conftest import record_by_id
from sqlalchemy import func, select

from reality.db.core import BusinessEvent, Document, DocumentLine, LedgerEntry, Movement
from reality.services.core import InvalidOperation, NotFound, create_manual_order
from reality.services.delivery_actions import (
    delivery_proposal_detail,
    prepare_delivery_action,
    reconcile_delivery,
)
from reality.tools.application import approve_and_execute_proposal


def prepare(
    session, business, direction="sales", line=None, request="invoice-120", **changes
):
    if not line:
        result = create_manual_order(
            session,
            business.tenant.id,
            direction,
            "ORDER-120",
            business.company.id,
            business.customer.id if direction == "sales" else business.supplier.id,
            business.location.id,
            [
                {
                    "item_id": business.item.id,
                    "quantity": "3",
                    "unit_price": "100",
                    "gross_amount": "300",
                }
            ],
            gross_amount="300",
        )
        line = result[2][0].id
    values = {
        "order_line_id": line,
        "quantity": "2",
        "gross_amount": "301",
        "number": "INV-120",
        "effective_at": "2026-09-08T12:00:00Z",
    }
    values.update(changes)
    return prepare_delivery_action(
        session,
        business.tenant.id,
        "sales_invoice_record" if direction == "sales" else "supplier_invoice_record",
        values,
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
def test_invoice_review_atomic_effects_and_unknown_recovery(
    session, business, direction
):
    proposal = prepare(session, business, direction)
    for model in (LedgerEntry, Movement):
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
    detail = delivery_proposal_detail(session, business.tenant.id, proposal.id)
    assert detail["verification"] == "verified"
    records = detail["receipt"]["records"]
    assert len(records) == 5
    invoice = record_by_id(
        session, Document, next(r["id"] for r in records if r["family"] == "document")
    )
    assert invoice.gross_amount == Decimal(301)
    entries = list(
        session.scalars(
            select(LedgerEntry).where(LedgerEntry.tenant_id == business.tenant.id)
        )
    )
    assert {(e.account, e.debit_credit, e.amount) for e in entries} == {
        (
            "accounts_receivable" if direction == "sales" else "inventory",
            "debit",
            Decimal(301),
        ),
        (
            "sales_revenue" if direction == "sales" else "accounts_payable",
            "credit",
            Decimal(301),
        ),
    }
    confirm(session, business, proposal)
    receipt = detail["receipt"]
    proposal.status = "executing"
    proposal.output = "{}"
    session.commit()
    assert (
        reconcile_delivery(session, business.tenant.id, proposal.id)["receipt"]
        == receipt
    )
    with pytest.raises(InvalidOperation, match="remaining"):
        prepare(
            session,
            business,
            direction,
            line=json.loads(proposal.input)["order_line_id"],
            request="again",
        )
    for model in (Movement,):
        assert (
            session.scalar(
                select(func.count())
                .select_from(model)
                .where(model.tenant_id == business.tenant.id)
            )
            == 0
        )


@pytest.mark.parametrize(
    "change", ["quantity", "gross_amount", "number", "order_line_id"]
)
def test_invalid_invoice_is_inert(session, business, change):
    with pytest.raises((InvalidOperation, NotFound)):
        prepare(
            session,
            business,
            **{
                change: {
                    "quantity": "4",
                    "gross_amount": "NaN",
                    "number": " ",
                    "order_line_id": "foreign",
                }[change]
            },
        )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_stale_line_and_unresolved_guard(session, business):
    proposal = prepare(session, business)
    line_id = json.loads(proposal.input)["order_line_id"]
    line = record_by_id(session, DocumentLine, line_id)
    line.gross_amount = Decimal(299)
    session.commit()
    with pytest.raises(InvalidOperation, match="review"):
        confirm(session, business, proposal)
    next_proposal = prepare(session, business, line=line_id, request="fresh")
    next_proposal.status = "executing"
    session.commit()
    with pytest.raises(InvalidOperation, match="unresolved"):
        prepare(session, business, line=line_id, request="blocked")
    assert (
        reconcile_delivery(session, business.tenant.id, next_proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_receipt_requires_exact_attributed_proof(session, business):
    proposal = prepare(session, business)
    confirm(session, business, proposal)
    event = session.scalar(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == business.tenant.id,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "invoice.recorded",
        )
    )
    assert event is not None
    payload = json.loads(event.payload)
    payload["creation"]["gross_amount"] = "999"
    event.payload = json.dumps(payload)
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_historical_invoice_proof_survives_reversal_and_unverified_output(
    session, business
):
    from reality.services.core import reverse_ledger_posting_group

    proposal = prepare(session, business)
    confirm(session, business, proposal)
    receipt = json.loads(proposal.output)
    entry_id = next(
        r["id"] for r in receipt["records"] if r["family"] == "ledger_entry"
    )
    group = record_by_id(session, LedgerEntry, entry_id).posting_group_id
    reverse_ledger_posting_group(
        session, business.tenant.id, group, reason="Invoice entered in error"
    )
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "verified"
    )
    proposal.output = "{}"
    session.commit()
    assert (
        delivery_proposal_detail(session, business.tenant.id, proposal.id)[
            "verification"
        ]
        == "unresolved"
    )


def test_invoice_foreign_direction_and_current_actor(session, business):
    from types import SimpleNamespace

    from reality.services.core import create_tenant

    proposal = prepare(session, business)
    line_id = json.loads(proposal.input)["order_line_id"]
    with pytest.raises(InvalidOperation, match="purchase order"):
        prepare(
            session,
            business,
            direction="purchase",
            line=line_id,
            request="wrong-direction",
        )
    foreign = create_tenant(session, "Foreign invoice tenant")
    with pytest.raises(NotFound):
        prepare_delivery_action(
            session,
            foreign.id,
            "sales_invoice_record",
            json.loads(proposal.input)["_delivery_review"]["intent"],
            request_id="foreign",
        )
    with pytest.raises(NotFound):
        approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirmed=True,
            review_token=json.loads(proposal.input)["_delivery_review"]["token"],
            confirming_principal=SimpleNamespace(
                user_id="missing", is_platform_admin=False
            ),
        )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 0


def test_default_effective_time_and_two_proposals_for_same_line(session, business):
    first = prepare(session, business, effective_at=None)
    second = prepare(
        session,
        business,
        line=json.loads(first.input)["order_line_id"],
        request="second",
        effective_at=None,
    )
    confirm(session, business, first)
    assert (
        delivery_proposal_detail(session, business.tenant.id, first.id)["verification"]
        == "verified"
    )
    with pytest.raises(InvalidOperation, match="remaining"):
        confirm(session, business, second)
    assert second.status == "proposed"
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == 2


@pytest.mark.parametrize("tool", ["sales_invoice_record", "supplier_invoice_record"])
def test_invoice_prepare_http_uses_shared_review(session, business, tool):
    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.web.api import database_session
    from reality.web.app import app

    first = prepare(
        session, business, "sales" if tool == "sales_invoice_record" else "purchase"
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
                    "tool": tool,
                    "request_id": "http",
                    "arguments": json.loads(first.input)["_delivery_review"]["intent"],
                },
            )
            assert response.status_code == 200, response.text
            proposal = response.json()
            response = client.post(
                f"{base}/change-proposals/{proposal['id']}/approve",
                json={"confirmed": True, "review_token": proposal["review"]["token"]},
            )
            assert response.status_code == 200, response.text
            assert (
                client.get(f"{base}/delivery-actions/{proposal['id']}").json()[
                    "verification"
                ]
                == "verified"
            )
    finally:
        app.dependency_overrides.clear()
