"""Spec 356: one retained order confirmation owns its entire transaction."""
import json

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import func, select

from reality.db.core import Commitment, Document, DocumentLine, SourceRecord
from reality.services import core
from reality.services.delivery_actions import REVIEW_KEY
from reality.tools import application


def order_arguments(business, direction):
    return {"direction": direction, "number": "ATOMIC-ORDER",
            "company_party_id": business.company.id,
            "counterparty_id": business.customer.id if direction == "sales" else business.supplier.id,
            "location_id": business.location.id,
            "lines": [{"item_id": business.item.id, "quantity": "2", "unit_price": "3", "gross_amount": "5"}],
            "gross_amount": "5"}


@pytest.mark.parametrize("direction", ["sales", "purchase"])
@pytest.mark.parametrize("attack", ["changed", "repeated", "early_commit", "after_write_failure", "sibling_header", "sibling_stock"])
def test_order_callback_cannot_change_or_partially_settle_its_confirmation(session, business, monkeypatch, direction, attack):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, "order_create", order_arguments(business, direction))
    review = json.loads(proposal.input)[REVIEW_KEY]["token"]
    source_count = session.scalar(select(func.count()).select_from(SourceRecord).where(SourceRecord.tenant_id == tenant))
    original = application.create_manual_order
    def callback(db, company, **arguments):
        if attack == "changed":
            arguments["number"] = "UNREVIEWED-ORDER"
        result = original(db, company, **arguments)
        if attack == "repeated":
            original(db, company, **arguments)
        if attack == "early_commit":
            db.commit()
        if attack == "sibling_header":
            core.create_document(db, company, "sales_order", "UNREVIEWED", business.customer.id, "1", _commit=False)
        if attack == "sibling_stock":
            core.record_movement(db, company, "receipt", business.item.id, "1", to_location_id=business.location.id, _commit=False)
        if attack == "after_write_failure":
            raise RuntimeError("Failure after order evidence and promises")
        return result
    monkeypatch.setattr(application, "create_manual_order", callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        application.approve_and_execute_proposal(session, tenant, proposal.id,
            confirming_principal=owner, confirmed=True, review_token=review)
    session.rollback()
    assert session.scalar(select(func.count()).select_from(SourceRecord).where(SourceRecord.tenant_id == tenant)) == source_count
    for model in (Document, DocumentLine, Commitment):
        assert session.scalar(select(func.count()).select_from(model).where(model.tenant_id == tenant)) == 0


@pytest.mark.parametrize("field", ["action_id", "_action_id", "_commit"])
def test_public_order_cannot_claim_private_execution_fields(session, business, field):
    with pytest.raises(core.InvalidOperation) as refused:
        application.create_change_proposal(session, business.tenant.id, "order_create",
            {**order_arguments(business, "sales"), field: True})
    assert refused.value.code == "manual_order_fields_invalid"


@pytest.mark.parametrize("direction", ["sales", "purchase"])
def test_confirmed_order_keeps_source_values_and_replays_its_actual_receipt(session, business, direction):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, "order_create", order_arguments(business, direction))
    review = json.loads(proposal.input)[REVIEW_KEY]["token"]
    receipt = application.approve_and_execute_proposal(session, tenant, proposal.id,
        confirming_principal=owner, confirmed=True, review_token=review)
    result = json.loads(receipt.output)
    source = session.scalar(select(SourceRecord).where(SourceRecord.tenant_id == tenant, SourceRecord.id == result["source_record_id"]))
    document = session.scalar(select(Document).where(Document.tenant_id == tenant, Document.id == result["document_id"]))
    line = session.scalar(select(DocumentLine).where(DocumentLine.tenant_id == tenant, DocumentLine.document_id == document.id))
    assert receipt.status == "executed" and receipt.decided_by_user_id == owner.user_id
    assert document.source_record_id == source.id
    assert json.loads(source.payload)["gross_amount"] == "5"
    assert document.gross_amount == line.gross_amount == 5
    assert line.quantity == 2 and line.unit_price == 3
    assert len(result["commitment_ids"]) == 1
    assert application.approve_and_execute_proposal(session, tenant, proposal.id,
        confirming_principal=owner, confirmed=True, review_token=review).output == receipt.output
    assert session.scalar(select(func.count()).select_from(Document).where(Document.tenant_id == tenant)) == 1
