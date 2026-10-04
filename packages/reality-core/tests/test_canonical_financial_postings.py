"""Spec 356: existing standalone financial parents own one actual decision."""

import json
from decimal import Decimal

import pytest
from intake_review_support import explicit_owner
from test_canonical_payment_boundary import state

from reality.db.core import Document, LedgerEntry, SettlementAllocation
from reality.services import core
from reality.tools import application

OPERATIONS = {
    "sales_invoice_post": ("post_sales_invoice", "sales_invoice", "document_id"),
    "supplier_invoice_post": (
        "post_supplier_invoice",
        "supplier_invoice",
        "document_id",
    ),
    "credit_note_post": ("post_sales_credit_note", "credit_note", "credit_note_id"),
    "supplier_credit_note_post": (
        "post_supplier_credit_note",
        "supplier_credit_note",
        "credit_note_id",
    ),
    "credit_note_allocate": ("allocate_credit_note", "credit_note", "credit_note_id"),
    "supplier_credit_note_allocate": (
        "allocate_supplier_credit_note",
        "supplier_credit_note",
        "credit_note_id",
    ),
    "supplier_refund_post": (
        "post_supplier_refund",
        "supplier_credit_note",
        "credit_note_id",
    ),
}


def approve(session, tenant, tool, values):
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, values)
    return application.approve_and_execute_proposal(
        session, tenant, proposal.id, confirming_principal=owner, confirmed=True
    )


def case(session, business, tool):
    _, kind, identity = OPERATIONS[tool]
    supplier = kind.startswith("supplier")
    party = business.supplier if supplier else business.customer
    document = core.create_document(
        session,
        business.tenant.id,
        kind,
        core.uid("CURRENT-FINANCIAL"),
        party.id,
        "90.1234",
    )
    arguments = {identity: document.id}
    if tool.endswith("allocate") or tool == "supplier_refund_post":
        approve(
            session,
            business.tenant.id,
            "supplier_credit_note_post" if supplier else "credit_note_post",
            arguments,
        )
        arguments["amount"] = "7.1234"
        if tool.endswith("allocate"):
            invoice = core.create_document(
                session,
                business.tenant.id,
                "supplier_invoice" if supplier else "sales_invoice",
                core.uid("CURRENT-INVOICE"),
                party.id,
                "90.1234",
            )
            approve(
                session,
                business.tenant.id,
                "supplier_invoice_post" if supplier else "sales_invoice_post",
                {"document_id": invoice.id},
            )
            arguments["invoice_id"] = invoice.id
        else:
            arguments["refund_number"] = "ACTUAL-SUPPLIER-REFUND"
    return arguments


def prepared(session, business, tool, values):
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(
        session, business.tenant.id, tool, values
    )
    return owner, proposal


@pytest.mark.parametrize("tool", OPERATIONS)
def test_standalone_financial_parent_requires_actual_retained_decision(
    session, business, tool
):
    values = case(session, business, tool)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation, match="(?i)approval|decision|confirm"):
        getattr(core, OPERATIONS[tool][0])(
            session, business.tenant.id, **values, _commit=False
        )
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_standalone_financial_no_confirmation_creates_no_claim_or_effect(
    session, business, tool
):
    values = case(session, business, tool)
    owner, proposal = prepared(session, business, tool, values)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation, match="(?i)approval|decision|confirm"):
        application.approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirming_principal=owner
        )
    session.refresh(proposal)
    assert proposal.status == "proposed" and proposal.decided_at is None
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize(
    "tool,attack",
    [
        (tool, attack)
        for tool in OPERATIONS
        for attack in (
            "changed",
            "repeated",
            "early_commit",
            "after_write_failure",
            "sibling_header",
            "sibling_stock",
            "changed_ledger",
            "changed_allocation",
            "changed_current_document",
        )
        if not (attack == "changed_ledger" and tool.endswith("allocate"))
        and not (
            attack == "changed_allocation"
            and not (tool.endswith("allocate") or tool == "supplier_refund_post")
        )
    ],
)
def test_standalone_financial_callback_is_exact_current_and_atomic(
    session, business, monkeypatch, tool, attack
):
    values = case(session, business, tool)
    owner, proposal = prepared(session, business, tool, values)
    before = state(session, business.tenant.id)
    operation = OPERATIONS[tool][0]
    original = getattr(core, operation)
    if attack in {"changed_ledger", "changed_allocation"}:
        child = "post_ledger" if attack == "changed_ledger" else "allocate_settlement"
        original_child = getattr(core, child)

        def changed(db, tenant, *args, **arguments):
            if child == "post_ledger":
                if args:
                    args = (
                        *args[:2],
                        [(role, side, "8.1234") for role, side, _ in args[2]],
                        *args[3:],
                    )
                else:
                    arguments["postings"] = [
                        (role, side, "8.1234")
                        for role, side, _ in arguments["postings"]
                    ]
            elif args:
                args = (*args[:2], "6.1234", *args[3:])
            else:
                arguments["amount"] = "6.1234"
            return original_child(db, tenant, *args, **arguments)

        monkeypatch.setattr(core, child, changed)

    def callback(db, tenant, **arguments):
        if attack == "changed":
            if "amount" in arguments:
                arguments["amount"] = "8.1234"
            else:
                arguments["effective_at"] = core.utc_datetime(
                    "2026-10-04T12:00:00+00:00"
                )
        if attack == "early_commit":
            db.commit()
        if attack == "changed_current_document":
            document = db.get(Document, (tenant, values[OPERATIONS[tool][2]]))
            document.number = "CHANGED-AFTER-DISPATCH"
            db.flush()
        result = original(db, tenant, **arguments)
        if attack == "repeated":
            original(db, tenant, **arguments)
        if attack == "after_write_failure":
            raise RuntimeError("The actual callback failed after writing")
        if attack == "sibling_header":
            core.create_document(
                db,
                tenant,
                "sales_order",
                "UNRELATED-FINANCIAL",
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

    monkeypatch.setattr(application, operation, callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        application.approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=owner,
            confirmed=True,
        )
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_standalone_financial_actual_person_values_receipt_and_replay(
    session, business, tool
):
    values = case(session, business, tool)
    owner, proposal = prepared(session, business, tool, values)
    receipt = application.approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=owner,
        confirmed=True,
    )
    assert receipt.status == "executed" and receipt.decided_by_user_id == owner.user_id
    records = json.loads(receipt.output)["records"]
    for record in records:
        model = (
            SettlementAllocation
            if record["family"] == "settlement_allocation"
            else LedgerEntry
        )
        row = session.get(model, (business.tenant.id, record["id"]))
        assert row is not None
        assert Decimal(row.amount) == Decimal(values.get("amount", "90.1234"))
    before = state(session, business.tenant.id)
    replay = application.approve_and_execute_proposal(
        session,
        business.tenant.id,
        proposal.id,
        confirming_principal=owner,
        confirmed=True,
    )
    assert replay.output == receipt.output
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("change", ["grant_revoke", "credential_revoke"])
def test_standalone_financial_rechecks_actual_oauth_consent(
    session, business, scheduled_owner, monkeypatch, tool, change
):
    from test_current_mcp_decision_authority import actual_confirmation_principal

    from reality.mcp.catalog import dispatch_mcp_tool

    values = case(session, business, tool)
    grant, credential, principal = actual_confirmation_principal(
        session, business, scheduled_owner
    )
    proposal = application.create_change_proposal(
        session, business.tenant.id, tool, values
    )
    before = state(session, business.tenant.id)
    operation = OPERATIONS[tool][0]
    original = getattr(core, operation)

    def callback(db, tenant, **arguments):
        actual = grant if change == "grant_revoke" else credential
        actual.revoked_at = core.now()
        db.flush()
        return original(db, tenant, **arguments)

    monkeypatch.setattr(application, operation, callback)
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


HTTP_PATHS = {
    "sales_invoice_post": "sales-invoices/postings",
    "supplier_invoice_post": "supplier-invoices/postings",
    "credit_note_post": "credit-notes/postings",
    "supplier_credit_note_post": "supplier-credit-notes/postings",
    "credit_note_allocate": "credit-notes/allocations",
    "supplier_credit_note_allocate": "supplier-credit-notes/allocations",
    "supplier_refund_post": "supplier-refunds",
}


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("confirmed", [False, True])
def test_standalone_financial_http_retains_actual_request_confirmation(
    session, business, monkeypatch, tool, confirmed
):
    from datetime import timedelta

    from fastapi.testclient import TestClient
    from sqlalchemy import select
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import UserSession, now, uid
    from reality.web import api, app, auth

    values = case(session, business, tool)
    owner = explicit_owner(session, business.tenant.id)
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    for module in (api, app, auth):
        monkeypatch.setattr(module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    token = uid("actual_financial_cookie")
    session.add(
        UserSession(
            id=uid("ses"),
            user_id=owner.user_id,
            token_hash=auth.digest(token),
            expires_at=now() + timedelta(days=1),
        )
    )
    session.commit()
    before = state(session, business.tenant.id)
    previous = set(
        session.scalars(
            select(core.ChangeProposal.id).where(
                core.ChangeProposal.tenant_id == business.tenant.id
            )
        )
    )
    if confirmed:
        values["confirmed"] = True
    with TestClient(app.app) as browser:
        browser.cookies.set(auth.COOKIE_NAME, token)
        response = browser.post(
            f"/api/tenants/{business.tenant.id}/finance/{HTTP_PATHS[tool]}", json=values
        )
    session.expire_all()
    proposals = list(
        session.scalars(
            select(core.ChangeProposal).where(
                core.ChangeProposal.tenant_id == business.tenant.id,
                core.ChangeProposal.id.not_in(previous),
            )
        )
    )
    if not confirmed:
        assert response.status_code == 400, response.text
        assert not proposals
        assert state(session, business.tenant.id) == before
    else:
        assert response.status_code == 201, response.text
        assert len(proposals) == 1 and proposals[0].status == "executed"
        assert proposals[0].decided_by_user_id == owner.user_id
        if tool.endswith("allocate"):
            assert (
                response.json()["id"]
                == json.loads(proposals[0].output)["records"][0]["id"]
            )
        else:
            assert len(response.json()["ledger_entry_ids"]) == 2


@pytest.mark.parametrize("tool", OPERATIONS)
def test_standalone_financial_rejects_caller_private_review(session, business, tool):
    values = case(session, business, tool)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        application.create_change_proposal(
            session,
            business.tenant.id,
            tool,
            {**values, "_financial_posting_review": {"fabricated": True}},
        )
    assert refused.value.code == "intake_review_invalid"
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize(
    "tool", [tool for tool in OPERATIONS if not tool.endswith("allocate")]
)
def test_standalone_financial_retains_public_defaults_before_confirmation(
    session, business, tool
):
    values = case(session, business, tool)
    _, proposal = prepared(session, business, tool, values)
    retained = json.loads(proposal.input)
    assert retained["effective_at"] is None
    if tool == "supplier_invoice_post":
        assert retained["exchange_rate"] is None
    assert "action_id" not in retained and "_commit" not in retained


@pytest.mark.parametrize("tool", OPERATIONS)
def test_standalone_financial_renews_after_actual_partner_role_decision(
    session, business, tool
):
    from intake_review_support import reviewed_update_party

    from reality.db.core import Party

    values = case(session, business, tool)
    owner, proposal = prepared(session, business, tool, values)
    document = session.get(Document, (business.tenant.id, values[OPERATIONS[tool][2]]))
    party = session.get(Party, (business.tenant.id, document.party_id))
    original = {
        column.name: getattr(party, column.name) for column in Party.__table__.columns
    }
    reviewed_update_party(
        session,
        business.tenant.id,
        party.id,
        party.name,
        party.type,
        roles=["customer", "supplier"],
    )
    session.refresh(party)
    assert {
        column.name: getattr(party, column.name) for column in Party.__table__.columns
    } == original
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation, match="(?i)changed|review|stale"):
        application.approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=owner,
            confirmed=True,
        )
    assert state(session, business.tenant.id) == before
