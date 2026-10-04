"""Spec 356: confirmed customer credit owns exact atomic effects."""

import json

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import func, select
from test_unified_invoice_credit import arguments, fixture

from reality.db.core import (
    Document,
    DocumentLine,
    LedgerEntry,
    SettlementAllocation,
    SourceRecord,
)
from reality.services import core
from reality.services.delivery_actions import REVIEW_KEY
from reality.tools import application


def prepared(session, business):
    invoice, lines = fixture(session, business)
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(
        session, business.tenant.id, "sales_credit_record", arguments(invoice, lines)
    )
    review = json.loads(proposal.input).get(REVIEW_KEY)
    return owner, proposal, review


def counts(session, tenant):
    return {
        model: session.scalar(
            select(func.count()).select_from(model).where(model.tenant_id == tenant)
        )
        for model in (
            Document,
            DocumentLine,
            LedgerEntry,
            SettlementAllocation,
            SourceRecord,
        )
    }


def execute(session, tenant, owner, proposal, review):
    return application.approve_and_execute_proposal(
        session,
        tenant,
        proposal.id,
        confirming_principal=owner,
        confirmed=True,
        review_token=review["token"] if review else None,
    )


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
def test_customer_credit_callback_cannot_escape_or_partially_settle(
    session, business, monkeypatch, attack
):
    tenant = business.tenant.id
    owner, proposal, review = prepared(session, business)
    baseline = counts(session, tenant)
    original = application.record_sales_credit

    def callback(db, company, **values):
        if attack == "changed":
            values["number"] = "UNREVIEWED-CREDIT"
        result = original(db, company, **values)
        if attack == "repeated":
            original(db, company, **values)
        if attack == "early_commit":
            db.commit()
        if attack == "after_write_failure":
            raise RuntimeError("Failure after credit evidence and posting")
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
        return result

    monkeypatch.setattr(application, "record_sales_credit", callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        execute(session, tenant, owner, proposal, review)
    session.rollback()
    assert counts(session, tenant) == baseline


def test_confirmed_customer_credit_preserves_statement_and_actual_receipt_replay(
    session, business
):
    from decimal import Decimal

    tenant = business.tenant.id
    owner, proposal, review = prepared(session, business)
    result = execute(session, tenant, owner, proposal, review)
    receipt = json.loads(proposal.output)
    note_id = next(
        row["id"] for row in receipt["records"] if row["family"] == "document"
    )
    note = session.scalar(
        select(Document).where(Document.tenant_id == tenant, Document.id == note_id)
    )
    assert note.gross_amount == Decimal("90.1234")
    rows = session.scalars(
        select(DocumentLine).where(
            DocumentLine.tenant_id == tenant, DocumentLine.document_id == note.id
        )
    ).all()
    assert len(rows) == 2
    assert all(row.gross_amount == Decimal("31.1234") for row in rows)
    source = session.scalar(
        select(SourceRecord).where(
            SourceRecord.tenant_id == tenant, SourceRecord.id == note.source_record_id
        )
    )
    assert json.loads(source.payload)["reason"] == "Agreed invoice correction"
    assert proposal.decided_by_user_id == owner.user_id
    baseline = counts(session, tenant)
    assert execute(session, tenant, owner, proposal, review) == result
    assert json.loads(proposal.output) == receipt
    assert counts(session, tenant) == baseline


@pytest.mark.parametrize("operation", ["post_ledger", "allocate_settlement"])
@pytest.mark.parametrize("attack", ["changed", "repeated"])
def test_customer_credit_child_callback_requires_exact_unused_invocation(
    session, business, monkeypatch, operation, attack
):
    tenant = business.tenant.id
    owner, proposal, review = prepared(session, business)
    baseline = counts(session, tenant)
    original = getattr(core, operation)

    def callback(db, company, *args, **values):
        if attack == "changed":
            if operation == "post_ledger":
                if args:
                    args = (
                        *args[:2],
                        [(account, side, "19") for account, side, _ in args[2]],
                    )
                else:
                    values["postings"] = [
                        (account, side, "19") for account, side, _ in values["postings"]
                    ]
            elif args:
                args = (*args[:2], "19")
            else:
                values["amount"] = "19"
        result = original(db, company, *args, **values)
        if attack == "repeated":
            original(db, company, *args, **values)
        return result

    monkeypatch.setattr(core, operation, callback)
    with pytest.raises(core.InvalidOperation) as refused:
        execute(session, tenant, owner, proposal, review)
    assert refused.value.code in {"intake_review_invalid", "intake_approval_required"}
    session.rollback()
    assert counts(session, tenant) == baseline
