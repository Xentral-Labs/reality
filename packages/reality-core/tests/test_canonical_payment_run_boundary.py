"""Spec 356: the explicit payment list and total share an actual atomic decision."""

import json
from decimal import Decimal

import pytest
from intake_review_support import explicit_owner, reviewed_record_supplier_invoice
from sqlalchemy import select
from test_canonical_payment_boundary import state
from test_multi_position_invoices import intent, order

from reality.db.core import Document
from reality.services import core
from reality.services.delivery_actions import REVIEW_KEY
from reality.tools import application


def case(session, business):
    payments = []
    for index in range(2):
        arguments = intent(order(session, business, "purchase"))
        arguments["number"] = f"SELECTED-RUN-INVOICE-{index}"
        result = reviewed_record_supplier_invoice(
            session, business.tenant.id, **arguments
        )
        identity = next(
            row["id"] for row in result["records"] if row["family"] == "document"
        )
        payments.append(
            {
                "invoice_id": identity,
                "amount": "7.1234",
                "payment_number": f"SELECTED-RUN-PAY-{index}",
            }
        )
    return {
        "payments": payments,
        "currency": "EUR",
        "expected_total": "14.2468",
        "reason": "These explicitly selected invoices",
    }


def prepare(session, business, values):
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(
        session, business.tenant.id, "payment_run", values
    )
    return owner, proposal


def execute(session, business, owner, proposal, *, confirmed=True):
    return application.approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=owner,
        confirmed=confirmed,
    )


def test_payment_run_canonical_parent_requires_actual_retained_confirmation(
    session, business
):
    values = case(session, business)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation, match="(?i)approval|decision|confirm"):
        core.execute_payment_run(session, business.tenant.id, **values)
    assert state(session, business.tenant.id) == before


def test_payment_run_without_confirmation_creates_no_claim_or_business_effect(
    session, business
):
    values = case(session, business)
    owner, proposal = prepare(session, business, values)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation, match="(?i)approval|decision|confirm"):
        execute(session, business, owner, proposal, confirmed=False)
    session.refresh(proposal)
    assert proposal.status == "proposed" and proposal.decided_at is None
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize(
    "attack",
    [
        "changed",
        "repeated",
        "early_commit",
        "after_write_failure",
        "partial_child_failure",
        "changed_child",
        "sibling_header",
        "sibling_stock",
    ],
)
def test_payment_run_callback_cannot_change_extend_or_partially_settle_selection(
    session, business, monkeypatch, attack
):
    values = case(session, business)
    owner, proposal = prepare(session, business, values)
    before = state(session, business.tenant.id)
    original = core.execute_payment_run
    child_original = core.post_supplier_payment
    calls = 0
    if attack in {"partial_child_failure", "changed_child"}:

        def child(db, tenant, *args, **arguments):
            nonlocal calls
            calls += 1
            if attack == "partial_child_failure" and calls == 2:
                raise RuntimeError("The second actual payment failed")
            if attack == "changed_child":
                if args:
                    args = (args[0], "8.1234", *args[2:])
                else:
                    arguments["amount"] = "8.1234"
            return child_original(db, tenant, *args, **arguments)

        monkeypatch.setattr(core, "post_supplier_payment", child)

    def callback(db, tenant, **arguments):
        if attack == "changed":
            arguments["payments"] = [
                {**row, "amount": "8.1234"} for row in arguments["payments"]
            ]
            arguments["expected_total"] = "16.2468"
        if attack == "early_commit":
            db.commit()
        result = original(db, tenant, **arguments)
        if attack == "repeated":
            original(db, tenant, **arguments)
        if attack == "after_write_failure":
            raise RuntimeError("Run callback failed after writing the complete run")
        if attack == "sibling_header":
            core.create_document(
                db,
                tenant,
                "sales_order",
                "UNRELATED-RUN",
                business.customer.id,
                "97",
                _commit=False,
            )
        if attack == "sibling_stock":
            core.record_movement(
                db,
                tenant,
                "receipt",
                business.item.id,
                "1",
                to_location_id=business.location.id,
                _commit=False,
            )
        return result

    monkeypatch.setattr(application, "execute_payment_run", callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        execute(session, business, owner, proposal)
    session.rollback()
    assert state(session, business.tenant.id) == before


def test_payment_run_requires_renewed_review_after_a_real_selected_invoice_payment(
    session, business
):
    values = case(session, business)
    owner, proposal = prepare(session, business, values)
    other = application.create_change_proposal(
        session,
        business.tenant.id,
        "supplier_payment_post",
        {
            "invoice_id": values["payments"][0]["invoice_id"],
            "amount": "1",
            "payment_number": "SEPARATELY-CONFIRMED",
        },
    )
    token = json.loads(other.input)[REVIEW_KEY]["token"]
    application.approve_and_execute_proposal(
        session,
        business.tenant.id,
        other.id,
        confirming_principal=owner,
        confirmed=True,
        review_token=token,
    )
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation, match="(?i)changed|review|context"):
        execute(session, business, owner, proposal)
    assert state(session, business.tenant.id) == before


def test_payment_run_preserves_actual_person_exact_selection_total_and_replay(
    session, business
):
    values = case(session, business)
    owner, proposal = prepare(session, business, values)
    receipt = execute(session, business, owner, proposal)
    assert receipt.status == "executed" and receipt.decided_by_user_id == owner.user_id
    output = json.loads(receipt.output)
    assert output["paid"] == 2 and Decimal(output["total"]) == Decimal(
        values["expected_total"]
    )
    assert [
        (row["invoice_id"], Decimal(row["amount"])) for row in output["payments"]
    ] == [(row["invoice_id"], Decimal(row["amount"])) for row in values["payments"]]
    documents = list(
        session.scalars(
            select(Document).where(
                Document.tenant_id == business.tenant.id,
                Document.type == "supplier_payment",
            )
        )
    )
    assert len(documents) == 2
    assert {row.number for row in documents} == {
        row["payment_number"] for row in values["payments"]
    }
    assert {row.gross_amount for row in documents} == {Decimal("7.1234")}
    before = state(session, business.tenant.id)
    replay = execute(session, business, owner, proposal)
    assert replay.id == receipt.id and state(session, business.tenant.id) == before


@pytest.mark.parametrize("change", ["grant_revoke", "credential_revoke"])
def test_payment_run_rechecks_actual_interactive_consent_after_dispatch(
    session, business, scheduled_owner, monkeypatch, change
):
    from test_current_mcp_decision_authority import actual_confirmation_principal

    from reality.mcp.catalog import dispatch_mcp_tool

    values = case(session, business)
    grant, credential, principal = actual_confirmation_principal(
        session, business, scheduled_owner
    )
    proposal = application.create_change_proposal(
        session, business.tenant.id, "payment_run", values
    )
    before = state(session, business.tenant.id)
    original = core.execute_payment_run

    def callback(db, company, **arguments):
        actual = grant if change == "grant_revoke" else credential
        actual.revoked_at = core.now()
        db.flush()
        return original(db, company, **arguments)

    monkeypatch.setattr(application, "execute_payment_run", callback)
    with pytest.raises(core.InvalidOperation) as refused:
        dispatch_mcp_tool(
            session,
            principal,
            "proposal_approve_and_execute",
            {"proposal_id": proposal.id, "approved": True},
        )
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, business.tenant.id) == before
