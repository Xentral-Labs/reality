"""Spec 352: reviewed shop evidence never manufactures a received amount."""

import json
from pathlib import Path

from sqlalchemy import select

from reality.db.core import Commitment, DocumentLine
from reality.services.core import enqueue_shopify_order
from reality.services.intake import apply_prepared_intake, prepare_intake, review_intake

FIXTURE = Path(__file__).parents[1] / "fixtures/shopify/order_10473.json"


def test_unknown_and_unstated_lines_are_visible(session, business):
    payload = json.loads(FIXTURE.read_text())
    source, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    line = review["plan"]["effects"][0]["arguments"]["lines"][0]
    assert line["unit_price"] == "49.00"
    assert line["gross_amount"] is None
    assert "line:0:amount_unstated" in review["plan"]["issues"]
    apply_prepared_intake(
        session, business.tenant.id, proposal.id, review["digest"], confirmed=True
    )
    accepted = session.scalar(select(DocumentLine))
    assert accepted.gross_amount is None
    assert accepted.unit_price == 49
    assert session.scalar(select(Commitment)).amount is None
    assert json.loads(source.payload) == payload


def test_manual_entry_cannot_claim_source_absence(session, business):
    import pytest

    from reality.services.core import (
        InvalidOperation,
        create_manual_document_with_lines,
    )

    with pytest.raises(InvalidOperation):
        create_manual_document_with_lines(
            session,
            business.tenant.id,
            "sales_order",
            "manual",
            business.customer.id,
            [
                {
                    "sku": "BIKE-LIGHT",
                    "quantity": "1",
                    "unit_price": "49",
                    "gross_amount": None,
                }
            ],
            "49",
        )
    with pytest.raises(InvalidOperation):
        create_manual_document_with_lines(
            session,
            business.tenant.id,
            "sales_order",
            "manual",
            business.customer.id,
            [
                {
                    "sku": "BIKE-LIGHT",
                    "quantity": "1",
                    "unit_price": "49",
                    "gross_amount": None,
                }
            ],
            "49",
            _carry_unstated_amount=True,
        )


def test_received_zero_and_inconsistent_amounts_remain_as_stated(session, business):
    payload = json.loads(FIXTURE.read_text())
    payload["line_items"][0]["total_price"] = "0"
    _, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert review["plan"]["effects"][0]["arguments"]["lines"][0]["gross_amount"] == "0"
    assert review["plan"]["effects"][0]["arguments"]["gross_amount"] == "1470.00"
    apply_prepared_intake(
        session, business.tenant.id, proposal.id, review["digest"], confirmed=True
    )
    assert session.scalar(select(DocumentLine)).gross_amount == 0


def test_unknown_amount_is_excluded_from_credit_total(session, business):
    from reality.services.credit_exposure import credit_exposure

    payload = json.loads(FIXTURE.read_text())
    _, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    apply_prepared_intake(
        session, business.tenant.id, proposal.id, review["digest"], confirmed=True
    )
    exposure = credit_exposure(session, business.tenant.id, business.customer.id)
    assert exposure["open_orders"]["unpriced"]
    assert not exposure["open_orders"]["rows"]


def test_credit_hold_is_part_of_the_exact_review(session, business):
    from reality.db.core import CommitmentHold

    business.customer.credit_limit = 100
    session.flush()
    payload = json.loads(FIXTURE.read_text())
    _, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    review = review_intake(session, business.tenant.id, proposal.id)
    assert review["plan"]["effects"][-1]["operation"] == "credit_hold"
    assert session.scalar(select(CommitmentHold)) is None
    apply_prepared_intake(
        session, business.tenant.id, proposal.id, review["digest"], confirmed=True
    )
    assert session.scalar(select(CommitmentHold)).reason_code == "credit_check"


def test_reductions_are_proposed_not_applied(session, business):
    from reality.db.core import CommitmentRevision
    from reality.services import core

    payload = json.loads(FIXTURE.read_text())
    _, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review_intake(session, business.tenant.id, proposal.id)["digest"],
        confirmed=True,
    )
    commitment = session.scalar(select(Commitment))
    payload["updated_at"] = "2026-10-04T09:00:00Z"
    payload["line_items"][0]["current_quantity"] = 20
    _, changed_job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    changed = prepare_intake(session, business.tenant.id, changed_job.id)
    review = review_intake(session, business.tenant.id, changed.id)
    assert review["plan"]["effects"][0]["operation"] == "commitment_revision"
    assert core.commitment_quantity(session, business.tenant.id, commitment.id) == 30
    assert session.scalar(select(CommitmentRevision)) is None
    apply_prepared_intake(
        session, business.tenant.id, changed.id, review["digest"], confirmed=True
    )
    assert core.commitment_quantity(session, business.tenant.id, commitment.id) == 20


def test_refund_interpretation_waits_for_decision(session, business):
    from reality.db.core import CommitmentRevision, Document, LedgerEntry
    from reality.services import core

    payload = json.loads(FIXTURE.read_text())
    _, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review_intake(session, business.tenant.id, proposal.id)["digest"],
        confirmed=True,
    )
    refund = {
        "id": "refund-reviewed",
        "order_id": payload["id"],
        "created_at": "2026-10-03T12:00:00Z",
        "refund_line_items": [
            {
                "line_item_id": payload["line_items"][0]["id"],
                "quantity": 2,
                "subtotal": "98.00",
                "restock_type": "cancel",
            }
        ],
        "transactions": [
            {
                "id": "txn-1",
                "kind": "refund",
                "status": "success",
                "amount": "98.00",
                "currency": "EUR",
            }
        ],
    }
    _, refund_job = core.enqueue_source(
        session,
        business.tenant.id,
        "shopify",
        "refund",
        refund["id"],
        refund,
        context={},
    )
    prepared = prepare_intake(session, business.tenant.id, refund_job.id)
    review = review_intake(session, business.tenant.id, prepared.id)
    assert (
        session.scalar(select(Document).where(Document.type == "sales_refund")) is None
    )
    assert session.scalar(select(CommitmentRevision)) is None
    apply_prepared_intake(
        session, business.tenant.id, prepared.id, review["digest"], confirmed=True
    )
    assert (
        session.scalar(
            select(Document).where(Document.type == "sales_refund")
        ).gross_amount
        == 98
    )
    assert session.scalar(select(CommitmentRevision)) is not None
    assert session.scalar(select(LedgerEntry)) is None


def test_inspector_does_not_present_missing_source_amount_as_money(session, business):
    from reality.db.core import Document
    from reality.web.api import document_inspector

    payload = json.loads(FIXTURE.read_text())
    _, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    apply_prepared_intake(
        session,
        business.tenant.id,
        proposal.id,
        review_intake(session, business.tenant.id, proposal.id)["digest"],
        confirmed=True,
    )
    detail = document_inspector(
        session, business.tenant.id, session.scalar(select(Document)).id
    )
    assert detail["evidence_lines"][0]["gross_amount"] is None
    section = next(row for row in detail["sections"] if row["title"] == "Lines")
    assert not any(
        part["type"] == "money" for part in section["rows"][0]["display_parts"]
    )


def test_unknown_item_does_not_rematch_at_confirmation(session, business):

    payload = json.loads(FIXTURE.read_text())
    payload["line_items"][0]["sku"] = "UNKNOWN-AT-REVIEW"
    _, job = enqueue_shopify_order(
        session,
        business.tenant.id,
        payload,
        business.company.id,
        business.customer.id,
        business.location.id,
    )
    proposal = prepare_intake(session, business.tenant.id, job.id)
    digest = review_intake(session, business.tenant.id, proposal.id)["digest"]
    reviewed_create_item(session, business.tenant.id, "UNKNOWN-AT-REVIEW", "Added later")
    apply_prepared_intake(
        session, business.tenant.id, proposal.id, digest, confirmed=True
    )
    assert session.scalar(select(DocumentLine)).item_id is None
    assert session.scalar(select(Commitment)) is None


from intake_review_support import reviewed_create_item
