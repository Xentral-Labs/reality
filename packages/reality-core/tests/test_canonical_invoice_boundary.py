"""Spec 356: retained invoice confirmation owns evidence and postings."""

import json

import pytest
from intake_review_support import explicit_owner, reviewed_manual_order
from sqlalchemy import func, select

from reality.db.core import Document, DocumentLine, LedgerEntry, SourceRecord
from reality.services import core, invoice_actions
from reality.services.delivery_actions import REVIEW_KEY
from reality.tools import application


def invoice_arguments(session, business, family):
    if family == "free_supplier":
        return "supplier_invoice_free_record", {
            "supplier_id": business.supplier.id,
            "number": "ATOMIC-INVOICE",
            "currency": "EUR",
            "gross_amount": "5",
            "lines": [
                {
                    "description": "Stated service",
                    "line_type": "service",
                    "quantity": "1",
                    "unit_price": "5",
                    "gross_amount": "5",
                }
            ],
        }
    direction = "sales" if family == "sales" else "purchase"
    _, _, lines, _ = reviewed_manual_order(
        session,
        business.tenant.id,
        direction,
        "INVOICE-ORDER",
        business.company.id,
        business.customer.id if family == "sales" else business.supplier.id,
        business.location.id,
        [
            {
                "item_id": business.item.id,
                "quantity": "2",
                "unit_price": "3",
                "gross_amount": "5",
            }
        ],
        "5",
    )
    return f"{family}_invoice_record", {
        "order_line_id": lines[0].id,
        "quantity": "1",
        "gross_amount": "2",
        "number": "ATOMIC-INVOICE",
    }


@pytest.mark.parametrize("family", ["sales", "supplier", "free_supplier"])
@pytest.mark.parametrize(
    "attack",
    [
        "changed",
        "repeated",
        "early_commit",
        "after_write_failure",
        "sibling_header",
        "sibling_stock",
    ],
)
def test_invoice_callback_cannot_change_or_partially_settle_confirmation(
    session, business, monkeypatch, family, attack
):
    tenant = business.tenant.id
    tool, arguments = invoice_arguments(session, business, family)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, arguments)
    review = json.loads(proposal.input).get(REVIEW_KEY)
    models = (Document, DocumentLine, LedgerEntry, SourceRecord)
    counts = {
        model: session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in models
    }
    module = invoice_actions if family == "free_supplier" else application
    name = (
        "record_free_supplier_invoice"
        if family == "free_supplier"
        else f"record_{family}_invoice"
    )
    original = getattr(module, name)

    def callback(db, company, **values):
        if attack == "changed":
            values["number"] = "UNREVIEWED-INVOICE"
        result = original(db, company, **values)
        if attack == "repeated":
            original(db, company, **values)
        if attack == "early_commit":
            db.commit()
        if attack == "sibling_header":
            core.create_document(
                db,
                company,
                "sales_order",
                "UNREVIEWED",
                business.customer.id,
                "1",
                _commit=False,
            )
        if attack == "sibling_stock":
            core.record_movement(
                db,
                company,
                "receipt",
                business.item.id,
                "1",
                to_location_id=business.location.id,
                _commit=False,
            )
        if attack == "after_write_failure":
            raise RuntimeError("Failure after invoice evidence and posting")
        return result

    monkeypatch.setattr(module, name, callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        application.approve_and_execute_proposal(
            session,
            tenant,
            proposal.id,
            confirming_principal=owner,
            confirmed=True,
            review_token=review["token"] if review else None,
        )
    session.rollback()
    for model in models:
        assert (
            session.scalar(
                select(func.count()).select_from(model).where(model.tenant_id == tenant)
            )
            == counts[model]
        )


@pytest.mark.parametrize("family", ["sales", "supplier", "free_supplier"])
@pytest.mark.parametrize("attack", ["changed", "repeated"])
def test_invoice_posting_callback_cannot_change_or_repeat_the_stated_posting(
    session, business, monkeypatch, family, attack
):
    tenant = business.tenant.id
    tool, arguments = invoice_arguments(session, business, family)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, arguments)
    review = json.loads(proposal.input).get(REVIEW_KEY)
    original = core.post_ledger
    count = session.scalar(
        select(func.count())
        .select_from(LedgerEntry)
        .where(LedgerEntry.tenant_id == tenant)
    )

    def callback(db, company, document_id, party_id, postings, **values):
        if attack == "changed":
            postings = [(account, side, "19") for account, side, _ in postings]
        result = original(db, company, document_id, party_id, postings, **values)
        if attack == "repeated":
            original(db, company, document_id, party_id, postings, **values)
        return result

    monkeypatch.setattr(core, "post_ledger", callback)
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(
            session,
            tenant,
            proposal.id,
            confirming_principal=owner,
            confirmed=True,
            review_token=review["token"] if review else None,
        )
    assert refused.value.code in {"intake_review_invalid", "intake_approval_required"}
    session.rollback()
    assert (
        session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.tenant_id == tenant)
        )
        == count
    )


@pytest.mark.parametrize("family", ["sales", "supplier", "free_supplier"])
def test_confirmed_invoice_preserves_stated_amount_and_actual_receipt_replay(
    session, business, family
):
    from decimal import Decimal

    tenant = business.tenant.id
    tool, arguments = invoice_arguments(session, business, family)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, arguments)
    review = json.loads(proposal.input).get(REVIEW_KEY)
    receipt = application.approve_and_execute_proposal(
        session,
        tenant,
        proposal.id,
        confirming_principal=owner,
        confirmed=True,
        review_token=review["token"] if review else None,
    )
    records = json.loads(receipt.output)["records"]
    doc_id = next(row["id"] for row in records if row["family"] == "document")
    document = session.scalar(
        select(Document).where(Document.tenant_id == tenant, Document.id == doc_id)
    )
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant,
            SourceRecord.id == document.source_record_id,
        )
    )
    assert receipt.status == "executed" and receipt.decided_by_user_id == owner.user_id
    assert document.gross_amount == Decimal(arguments["gross_amount"])
    assert Decimal(json.loads(source.payload)["gross_amount"]) == document.gross_amount
    entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant, LedgerEntry.document_id == doc_id
            )
        )
    )
    assert len(entries) == 2 and all(
        row.amount == document.gross_amount for row in entries
    )
    replay = application.approve_and_execute_proposal(
        session,
        tenant,
        proposal.id,
        confirming_principal=owner,
        confirmed=True,
        review_token=review["token"] if review else None,
    )
    assert replay.id == receipt.id and replay.output == receipt.output
    assert (
        session.scalar(
            select(func.count())
            .select_from(LedgerEntry)
            .where(LedgerEntry.tenant_id == tenant, LedgerEntry.document_id == doc_id)
        )
        == 2
    )
