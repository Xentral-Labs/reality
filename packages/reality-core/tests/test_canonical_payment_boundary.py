"""Spec 356: retained selected payment/refund confirmation owns atomic effects."""

import inspect
import json
from dataclasses import replace
from decimal import Decimal

import pytest
from intake_review_support import (
    explicit_owner,
    reviewed_record_sales_credit,
    reviewed_record_sales_invoice,
    reviewed_record_supplier_invoice,
)
from sqlalchemy import select
from test_multi_position_invoices import intent, order

from reality.db.core import (
    BusinessEvent,
    Document,
    DocumentLine,
    LedgerEntry,
    Movement,
    SettlementAllocation,
    SourceRecord,
)
from reality.domain.intake import canonical_json
from reality.services import core
from reality.services.delivery_actions import REVIEW_KEY
from reality.tools import application

OPERATIONS = {
    "customer_payment_post": ("post_customer_payment", "record_customer_payment"),
    "supplier_payment_post": ("post_supplier_payment", "record_supplier_payment"),
    "customer_refund_post": ("post_customer_refund", "record_customer_refund"),
}


def case(session, business, tool):
    tenant = business.tenant.id
    supplier = tool == "supplier_payment_post"
    lines = order(session, business, "purchase" if supplier else "sales")
    recorder = (
        reviewed_record_supplier_invoice if supplier else reviewed_record_sales_invoice
    )
    result = recorder(session, tenant, **intent(lines))
    document_id = next(
        row["id"] for row in result["records"] if row["family"] == "document"
    )
    if tool == "customer_refund_post":
        invoice_lines = [
            row["id"] for row in result["records"] if row["family"] == "document_line"
        ]
        result = reviewed_record_sales_credit(
            session,
            tenant,
            invoice_id=document_id,
            lines=[
                {
                    "invoice_line_id": identity,
                    "quantity": "1",
                    "gross_amount": "31.1234",
                }
                for identity in invoice_lines
            ],
            gross_amount="90.1234",
            number="ACTUAL-CREDIT",
            reason="Agreed invoice correction",
            allocation_amount="0",
        )
        document_id = next(
            row["id"] for row in result["records"] if row["family"] == "document"
        )
    return {
        "credit_note_id"
        if tool == "customer_refund_post"
        else "invoice_id": document_id,
        "amount": "7.1234",
        "refund_number"
        if tool == "customer_refund_post"
        else "payment_number": "ACTUAL-SETTLEMENT",
        "effective_at": "2026-10-04T12:00:00+00:00",
    }


def state(session, tenant):
    return {
        model.__tablename__: canonical_json(
            [
                {
                    column.name: getattr(row, column.name)
                    for column in model.__table__.columns
                }
                for row in session.scalars(
                    select(model).where(model.tenant_id == tenant).order_by(model.id)
                )
            ]
        )
        for model in (
            Document,
            DocumentLine,
            LedgerEntry,
            SettlementAllocation,
            SourceRecord,
            BusinessEvent,
            Movement,
        )
    }


def prepare(session, tenant, tool, values):
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, values)
    return owner, proposal, json.loads(proposal.input)[REVIEW_KEY]["token"]


def execute(session, tenant, owner, proposal, token, *, confirmed=True):
    return application.approve_and_execute_proposal(
        session,
        tenant,
        proposal.id,
        confirming_principal=owner,
        confirmed=confirmed,
        review_token=token,
    )


@pytest.mark.parametrize("tool", OPERATIONS)
def test_selected_payment_canonical_parent_requires_actual_retained_confirmation(
    session, business, tool
):
    values = case(session, business, tool)
    values["effective_at"] = core.utc_datetime(values["effective_at"])
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation, match="(?i)approval|decision|confirm"):
        getattr(core, OPERATIONS[tool][0])(session, business.tenant.id, **values)
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_selected_payment_requires_explicit_confirmation_of_current_review(
    session, business, tool
):
    values = case(session, business, tool)
    owner, proposal, token = prepare(session, business.tenant.id, tool, values)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation):
        execute(session, business.tenant.id, owner, proposal, token, confirmed=False)
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize(
    "attack",
    [
        "changed",
        "repeated",
        "early_commit",
        "after_write_failure",
        "sibling_header",
        "sibling_stock",
        "changed_inner",
        "changed_ledger",
        "changed_allocation",
    ],
)
def test_selected_payment_callback_cannot_extend_or_partially_settle_its_review(
    session, business, monkeypatch, tool, attack
):
    values = case(session, business, tool)
    tenant = business.tenant.id
    owner, proposal, token = prepare(session, tenant, tool, values)
    operation, child = OPERATIONS[tool]
    original = getattr(core, operation)
    before = state(session, tenant)
    if attack == "changed_inner":
        child_original = getattr(core, child)

        def changed_child(*args, **kwargs):
            bound = inspect.signature(child_original).bind(*args, **kwargs)
            bound.arguments["amount"] = "8.1234"
            return child_original(*bound.args, **bound.kwargs)

        monkeypatch.setattr(core, child, changed_child)
    if attack in {"changed_ledger", "changed_allocation"}:
        callee = "post_ledger" if attack == "changed_ledger" else "allocate_settlement"
        callee_original = getattr(core, callee)

        def changed_financial_child(*args, **kwargs):
            bound = inspect.signature(callee_original).bind(*args, **kwargs)
            if attack == "changed_ledger":
                bound.arguments["postings"] = [
                    (role, side, "8.1234")
                    for role, side, _ in bound.arguments["postings"]
                ]
            else:
                bound.arguments["amount"] = "6.1234"
            return callee_original(*bound.args, **bound.kwargs)

        monkeypatch.setattr(core, callee, changed_financial_child)

    def callback(db, company, **arguments):
        if attack == "changed":
            arguments["amount"] = "8.1234"
        if attack == "early_commit":
            db.commit()
        result = original(db, company, **arguments)
        if attack == "repeated":
            original(db, company, **arguments)
        if attack == "after_write_failure":
            raise RuntimeError("Payment callback failed after the actual write")
        if attack == "sibling_header":
            core.create_document(
                db,
                company,
                "sales_order",
                "UNRELATED-PAYMENT",
                business.customer.id,
                "97",
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

    monkeypatch.setattr(application, operation, callback)
    if tool != "customer_refund_post":
        # Patch the actual captured service by rebuilding only its registered adapter.
        handler = application._payment(
            "supplier" if tool == "supplier_payment_post" else "customer"
        )
        monkeypatch.setitem(
            application.TOOLS, tool, replace(application.TOOLS[tool], handler=handler)
        )
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        execute(session, tenant, owner, proposal, token)
    session.rollback()
    assert state(session, tenant) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_selected_payment_keeps_exact_statement_person_allocation_and_receipt_replay(
    session, business, tool
):
    values = case(session, business, tool)
    tenant = business.tenant.id
    owner, proposal, token = prepare(session, tenant, tool, values)
    target_id = values.get("invoice_id") or values["credit_note_id"]
    opened = core.open_invoice_amount(session, tenant, target_id)
    receipt = execute(session, tenant, owner, proposal, token)
    assert receipt.status == "executed" and receipt.decided_by_user_id == owner.user_id
    entry_ids = [row["id"] for row in json.loads(receipt.output)["records"]]
    entries = list(
        session.scalars(
            select(LedgerEntry).where(
                LedgerEntry.tenant_id == tenant, LedgerEntry.id.in_(entry_ids)
            )
        )
    )
    assert len(entries) == 2
    assert {entry.amount for entry in entries} == {Decimal("7.1234")}
    allocation_event = session.scalars(
        select(BusinessEvent).where(
            BusinessEvent.tenant_id == tenant,
            BusinessEvent.action_id == proposal.id,
            BusinessEvent.event_type == "settlement.allocated",
        )
    ).one()
    allocations = list(
        session.scalars(
            select(SettlementAllocation).where(
                SettlementAllocation.tenant_id == tenant,
                SettlementAllocation.id == allocation_event.subject_id,
            )
        )
    )
    assert len(allocations) == 1 and allocations[0].amount == Decimal("7.1234")
    assert core.open_invoice_amount(session, tenant, target_id) == opened - Decimal(
        "7.1234"
    )
    before = state(session, tenant)
    replay = execute(session, tenant, owner, proposal, token)
    assert replay.id == receipt.id and state(session, tenant) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_selected_payment_rechecks_current_invoice_context_inside_its_canonical_callback(
    session, business, monkeypatch, tool
):
    values = case(session, business, tool)
    tenant = business.tenant.id
    owner, proposal, token = prepare(session, tenant, tool, values)
    operation = OPERATIONS[tool][0]
    original = getattr(core, operation)
    target_id = values.get("invoice_id") or values["credit_note_id"]
    before = state(session, tenant)

    def callback(db, company, **arguments):
        # Adversarial state change after dispatch; this is not a fabricated approval.
        document = db.get(Document, (company, target_id))
        document.number = "CONTEXT-CHANGED-AFTER-DISPATCH"
        db.flush()
        return original(db, company, **arguments)

    monkeypatch.setattr(application, operation, callback)
    if tool != "customer_refund_post":
        monkeypatch.setitem(
            application.TOOLS,
            tool,
            replace(
                application.TOOLS[tool],
                handler=application._payment(
                    "supplier" if tool == "supplier_payment_post" else "customer"
                ),
            ),
        )
    with pytest.raises(core.InvalidOperation, match="(?i)context|changed|review"):
        execute(session, tenant, owner, proposal, token)
    session.rollback()
    assert state(session, tenant) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_selected_payment_requires_renewed_review_after_actual_cash_default_decision(
    session, business, tool
):
    from intake_review_support import (
        reviewed_create_account,
        reviewed_set_default_account,
    )

    values = case(session, business, tool)
    tenant = business.tenant.id
    owner, proposal, token = prepare(session, tenant, tool, values)
    result = reviewed_create_account(
        session,
        tenant,
        code="SECOND-CASH",
        name="Separately reviewed cash",
        role="cash",
    )
    account_id = result["id"]
    reviewed_set_default_account(session, tenant, role="cash", account_id=account_id)
    before = state(session, tenant)
    with pytest.raises(core.InvalidOperation, match="(?i)context|changed|review"):
        execute(session, tenant, owner, proposal, token)
    assert state(session, tenant) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_selected_payment_retains_public_defaults_in_its_actual_review(
    session, business, tool
):
    values = case(session, business, tool)
    _, proposal, _ = prepare(session, business.tenant.id, tool, values)
    prepared = json.loads(proposal.input)
    assert prepared["source_record_id"] is None
    assert prepared[REVIEW_KEY]["intent"]["source_record_id"] is None
    assert "action_id" not in prepared and "_commit" not in prepared


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("change", ["grant_revoke", "credential_revoke"])
def test_selected_payment_rechecks_actual_interactive_consent_after_dispatch(
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
    token = json.loads(proposal.input)[REVIEW_KEY]["token"]
    before = state(session, business.tenant.id)
    operation = OPERATIONS[tool][0]
    original = getattr(core, operation)

    def callback(db, company, **arguments):
        actual = grant if change == "grant_revoke" else credential
        actual.revoked_at = core.now()
        db.flush()
        return original(db, company, **arguments)

    monkeypatch.setattr(application, operation, callback)
    if tool != "customer_refund_post":
        monkeypatch.setitem(
            application.TOOLS,
            tool,
            replace(
                application.TOOLS[tool],
                handler=application._payment(
                    "supplier" if tool == "supplier_payment_post" else "customer"
                ),
            ),
        )
    with pytest.raises(core.InvalidOperation) as refused:
        dispatch_mcp_tool(
            session,
            principal,
            "proposal_approve_and_execute",
            {"proposal_id": proposal.id, "approved": True, "review_token": token},
        )
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize(
    "tool",
    [
        "customer_payment_post",
        "supplier_payment_post",
        "customer_refund_post",
        "payment_run",
    ],
)
@pytest.mark.parametrize("confirmed", [False, True])
def test_payment_authenticated_http_retains_actual_confirmation(
    session, business, monkeypatch, tool, confirmed
):
    from datetime import timedelta

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker
    from test_canonical_payment_run_boundary import case as run_case

    from reality.db.core import UserSession, now, uid
    from reality.web import api, app, auth

    values = (
        run_case(session, business)
        if tool == "payment_run"
        else case(session, business, tool)
    )
    owner = explicit_owner(session, business.tenant.id)
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    for module in (api, app, auth):
        monkeypatch.setattr(module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    token = uid("actual_payment_cookie")
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
    suffix = {
        "customer_payment_post": "customer-payments",
        "supplier_payment_post": "supplier-payments",
        "customer_refund_post": "customer-refunds",
        "payment_run": "payment-runs",
    }[tool]
    with TestClient(app.app) as browser:
        browser.cookies.set(auth.COOKIE_NAME, token)
        response = browser.post(
            f"/api/tenants/{business.tenant.id}/finance/{suffix}", json=values
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
        assert "confirmed" not in response.json()
        if tool == "payment_run":
            assert response.json()["paid"] == 2
            assert Decimal(response.json()["total"]) == Decimal(
                values["expected_total"]
            )
        else:
            assert len(response.json()["ledger_entry_ids"]) == 2


@pytest.mark.parametrize("tool", ["customer_payment_post", "supplier_payment_post"])
@pytest.mark.parametrize("confirmed", [False, True])
def test_payment_cli_decline_or_yes_retains_real_unnamed_decision(
    session, business, monkeypatch, tool, confirmed
):
    from sqlalchemy.orm import sessionmaker
    from typer.testing import CliRunner

    from reality.cli import app as cli_module

    values = case(session, business, tool)
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    monkeypatch.setattr(cli_module, "Session", factory)
    monkeypatch.setattr(cli_module, "init_db", lambda: None)
    before = state(session, business.tenant.id)
    previous = set(
        session.scalars(
            select(core.ChangeProposal.id).where(
                core.ChangeProposal.tenant_id == business.tenant.id
            )
        )
    )
    command = "pay-customer" if tool == "customer_payment_post" else "pay-supplier"
    arguments = [
        "finance",
        command,
        values["invoice_id"],
        values["amount"],
        "--number",
        values["payment_number"],
        "--tenant",
        business.tenant.id,
    ]
    if confirmed:
        arguments.append("--yes")
    result = CliRunner().invoke(cli_module.app, arguments, input="n\n")
    assert result.exit_code == 0, result.stdout
    session.expire_all()
    proposals = list(
        session.scalars(
            select(core.ChangeProposal).where(
                core.ChangeProposal.tenant_id == business.tenant.id,
                core.ChangeProposal.id.not_in(previous),
            )
        )
    )
    assert len(proposals) == 1
    proposal = proposals[0]
    assert proposal.decided_by_user_id is None and proposal.decided_via_channel is None
    if confirmed:
        assert proposal.status == "executed"
        assert Decimal(json.loads(proposal.input)["amount"]) == Decimal(
            values["amount"]
        )
        assert proposal.decided_at is not None
    else:
        assert proposal.status == "proposed" and proposal.decided_at is None
        assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("fixed_tool", ["demo_seed", "normal_month"])
@pytest.mark.parametrize("selected_tool", ["customer_refund_post", "payment_run"])
def test_fixed_setup_cannot_borrow_refund_or_payment_run_family(
    session, business, monkeypatch, fixed_tool, selected_tool
):
    from test_canonical_payment_run_boundary import case as run_case

    from reality.services.intake import _invoke

    values = (
        run_case(session, business)
        if selected_tool == "payment_run"
        else case(session, business, selected_tool)
    )
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(
        session, business.tenant.id, fixed_tool, {}
    )
    before = state(session, business.tenant.id)
    operation = (
        "execute_payment_run"
        if selected_tool == "payment_run"
        else "post_customer_refund"
    )

    def callback(*args, **kwargs):
        _invoke(
            operation,
            getattr(core, operation),
            session,
            business.tenant.id,
            **values,
            _commit=False,
        )
        pytest.fail("An authored setup borrowed an unrelated financial family.")

    monkeypatch.setattr(
        application,
        "ensure_demo" if fixed_tool == "demo_seed" else "run_normal_month",
        callback,
    )
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(
            session,
            business.tenant.id,
            proposal.id,
            confirming_principal=owner,
            confirmed=True,
        )
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, business.tenant.id) == before
