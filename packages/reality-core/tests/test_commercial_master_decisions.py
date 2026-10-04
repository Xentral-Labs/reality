"""Spec 356: retained confirmation owns commercial master changes atomically."""

import json
from datetime import timedelta

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Document,
    PartyGroup,
    PartyGroupMember,
    PartyGroupPriceList,
    PartyPriceList,
    PaymentTerm,
    PriceList,
    PriceListEntry,
    SourceRecord,
    UserSession,
    now,
    uid,
)
from reality.services import core
from reality.tools import application

OPERATIONS = {
    "payment_term_create": ("create_payment_term", PaymentTerm),
    "payment_term_update": ("update_payment_term", PaymentTerm),
    "price_list_create": ("create_price_list", PriceList),
    "price_list_update": ("update_price_list", PriceList),
    "price_tier_create": ("create_price_list_entry", PriceListEntry),
    "party_price_list_assign": ("assign_party_price_list", PartyPriceList),
    "party_group_create": ("create_party_group", PartyGroup),
    "party_group_update": ("update_party_group", PartyGroup),
    "party_group_member_add": ("add_party_group_member", PartyGroupMember),
    "group_price_list_assign": ("assign_group_price_list", PartyGroupPriceList),
}


def http_route(tool, arguments):
    values = dict(arguments)
    if tool.startswith("payment_term"):
        path = "payment-terms"
        identity = values.pop("payment_term_id", None)
    elif tool.startswith("price_list"):
        path = "price-lists"
        identity = values.pop("price_list_id", None)
    elif tool == "price_tier_create":
        return "POST", "price-tiers", values
    elif tool == "party_price_list_assign":
        return "POST", f"parties/{values.pop('party_id')}/price-lists", values
    elif tool in {"party_group_create", "party_group_update"}:
        path = "pricing-groups"
        identity = values.pop("party_group_id", None)
    else:
        group = values.pop("party_group_id")
        suffix = "members" if tool == "party_group_member_add" else "price-lists"
        return "POST", f"pricing-groups/{group}/{suffix}", values
    return ("PUT", f"{path}/{identity}", values) if identity else ("POST", path, values)


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("confirmed", [False, True])
def test_authenticated_commercial_http_requires_explicit_person_confirmation(
    session, business, monkeypatch, tool, confirmed
):
    from fastapi.testclient import TestClient

    from reality.web import api, app, auth

    tenant = business.tenant.id
    arguments = case(session, business, tool)
    owner = explicit_owner(session, tenant)
    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    for module in (api, app, auth):
        monkeypatch.setattr(module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    token = uid("http_commercial")
    session.add(
        UserSession(
            id=uid("ses"),
            user_id=owner.user_id,
            token_hash=auth.digest(token),
            expires_at=now() + timedelta(days=1),
        )
    )
    session.commit()
    before = count(session, tenant)
    proposals_before = set(
        session.scalars(
            select(ChangeProposal.id).where(ChangeProposal.tenant_id == tenant)
        )
    )
    method, path, values = http_route(tool, arguments)
    if confirmed:
        values["confirmed"] = True
    with TestClient(app.app) as browser:
        browser.cookies.set(auth.COOKIE_NAME, token)
        response = browser.request(method, f"/api/tenants/{tenant}/{path}", json=values)
    session.expire_all()
    if not confirmed:
        assert response.status_code == 400, response.text
        assert "confirmation_required" in response.text
        assert count(session, tenant) == before
        assert (
            set(
                session.scalars(
                    select(ChangeProposal.id).where(ChangeProposal.tenant_id == tenant)
                )
            )
            == proposals_before
        )
    else:
        assert response.status_code == (200 if method == "PUT" else 201), response.text
        proposal = session.scalars(
            select(ChangeProposal).where(
                ChangeProposal.tenant_id == tenant,
                ChangeProposal.id.not_in(proposals_before),
            )
        ).one()
        assert proposal.decided_by_user_id == owner.user_id
        assert proposal.status == "executed"
        assert json.loads(proposal.output)["records"][0]["id"] == response.json()["id"]
        assert "confirmed" not in response.json()


@pytest.mark.parametrize("approved", [False, True])
def test_commercial_cli_retains_real_confirmation_without_inventing_a_person(
    session, business, monkeypatch, approved
):
    from typer.testing import CliRunner

    from reality.cli import app

    factory = sessionmaker(
        session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )
    monkeypatch.setattr(app, "Session", factory)
    monkeypatch.setattr(app, "init_db", lambda: None)
    arguments = [
        "payment-term",
        "create",
        "CLI14",
        "Exact CLI term",
        "14",
        "--tenant",
        business.tenant.id,
    ]
    if approved:
        arguments.append("--yes")
    result = CliRunner().invoke(app.app, arguments, input="n\n")
    assert result.exit_code == 0, result.output
    proposal = session.scalars(
        select(ChangeProposal).where(
            ChangeProposal.tenant_id == business.tenant.id,
                ChangeProposal.type == "tool:payment_term_create",
        )
    ).one()
    assert proposal.status == ("executed" if approved else "proposed")
    assert proposal.decided_by_user_id is None
    assert proposal.decided_via_channel is None
    term = session.scalars(
        select(PaymentTerm).where(
            PaymentTerm.tenant_id == business.tenant.id, PaymentTerm.code == "CLI14"
        )
    ).one_or_none()
    if approved:
        assert term is not None
        assert term.name == "Exact CLI term" and term.due_days == 14
        assert json.loads(proposal.output)["records"][0]["id"] == term.id
    else:
        assert term is None


def confirm(session, tenant, tool, arguments):
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, arguments)
    application.approve_and_execute_proposal(
        session, tenant, proposal.id, confirming_principal=owner, confirmed=True
    )
    return json.loads(proposal.output)["records"][0]["id"]


def case(session, business, tool):
    tenant = business.tenant.id
    explicit_owner(session, tenant)
    if tool.startswith("payment_term"):
        values = {
            "code": "NET14",
            "name": "Stated maturity",
            "due_days": 14,
            "discount_percent": "2",
            "discount_days": 7,
        }
        if tool.endswith("update"):
            values["payment_term_id"] = confirm(
                session, tenant, "payment_term_create", {**values, "code": "ORIGINAL"}
            )
        return values
    if tool.startswith("price_list"):
        values = {
            "code": "EUR1",
            "name": "Stated prices",
            "direction": "sales",
            "currency": "EUR",
        }
        if tool.endswith("update"):
            values["price_list_id"] = confirm(
                session, tenant, "price_list_create", {**values, "code": "ORIGINAL"}
            )
        return values
    if tool in {"party_group_create", "party_group_update"}:
        values = {"code": "GOLD", "name": "Stated group"}
        if tool.endswith("update"):
            values["party_group_id"] = confirm(
                session, tenant, "party_group_create", {**values, "code": "ORIGINAL"}
            )
        return values
    group = confirm(
        session, tenant, "party_group_create", {"code": "BASE", "name": "Actual group"}
    )
    price_list = confirm(
        session,
        tenant,
        "price_list_create",
        {
            "code": "BASE",
            "name": "Actual prices",
            "direction": "sales",
            "currency": "EUR",
        },
    )
    if tool == "price_tier_create":
        return {
            "price_list_id": price_list,
            "item_id": business.item.id,
            "min_quantity": "2",
            "unit_price": "7.1234",
            "unit": "pcs",
        }
    if tool == "party_group_member_add":
        return {"party_group_id": group, "party_id": business.customer.id}
    return {
        "price_list_id": price_list,
        "priority": 41,
        **(
            {"party_id": business.customer.id}
            if tool == "party_price_list_assign"
            else {"party_group_id": group}
        ),
    }


def count(session, tenant):
    from reality.domain.intake import canonical_json

    return {
        model: [
            canonical_json(
                {
                    column.name: getattr(row, column.name)
                    for column in model.__table__.columns
                }
            )
            for row in session.scalars(
                select(model).where(model.tenant_id == tenant).order_by(model.id)
            )
        ]
        for model in (
            PaymentTerm,
            PriceList,
            PriceListEntry,
            PartyGroup,
            PartyGroupMember,
            PartyGroupPriceList,
            PartyPriceList,
            Document,
            BusinessEvent,
            SourceRecord,
        )
    }


@pytest.mark.parametrize("tool", OPERATIONS)
def test_direct_commercial_master_write_requires_retained_decision(
    session, business, tool
):
    values = case(session, business, tool)
    baseline = count(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        getattr(core, OPERATIONS[tool][0])(session, business.tenant.id, **values)
    assert refused.value.code == "intake_approval_required"
    assert count(session, business.tenant.id) == baseline


@pytest.mark.parametrize("tool", OPERATIONS)
def test_commercial_master_requires_explicit_confirmation(session, business, tool):
    values = case(session, business, tool)
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(
        session, business.tenant.id, tool, values
    )
    baseline = count(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(
            session, business.tenant.id, proposal.id, confirming_principal=owner
        )
    assert refused.value.code == "review_confirmation_required"
    assert count(session, business.tenant.id) == baseline


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("private", ["_commit", "_commercial_master_review"])
def test_commercial_master_rejects_caller_execution_or_reference_proof(
    session, business, tool, private
):
    values = case(session, business, tool)
    with pytest.raises(core.InvalidOperation) as refused:
        application.create_change_proposal(
            session, business.tenant.id, tool, {**values, private: False}
        )
    assert refused.value.code == "intake_review_invalid"


@pytest.mark.parametrize(
    "tool",
    [
        "payment_term_update",
        "price_list_update",
        "party_group_update",
        "price_tier_create",
        "party_price_list_assign",
        "group_price_list_assign",
        "party_group_member_add",
    ],
)
def test_commercial_reference_changed_by_another_real_decision_requires_review(
    session, business, tool
):
    tenant = business.tenant.id
    values = case(session, business, tool)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, values)
    if "payment_term_id" in values:
        row = core._tenant_record_read(
            session, PaymentTerm, tenant, values["payment_term_id"]
        )
        confirm(
            session,
            tenant,
            "payment_term_update",
            {
                "payment_term_id": row.id,
                "code": row.code,
                "name": "Changed through a second decision",
                "due_days": row.due_days,
            },
        )
    elif "price_list_id" in values:
        row = core._tenant_record_read(
            session, PriceList, tenant, values["price_list_id"]
        )
        confirm(
            session,
            tenant,
            "price_list_update",
            {
                "price_list_id": row.id,
                "code": row.code,
                "name": "Changed through a second decision",
                "direction": row.direction,
                "currency": row.currency,
            },
        )
    else:
        row = core._tenant_record_read(
            session, PartyGroup, tenant, values["party_group_id"]
        )
        confirm(
            session,
            tenant,
            "party_group_update",
            {
                "party_group_id": row.id,
                "code": row.code,
                "name": "Changed through a second decision",
            },
        )
    baseline = count(session, tenant)
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(
            session, tenant, proposal.id, confirming_principal=owner, confirmed=True
        )
    assert refused.value.code == "intake_review_stale"
    session.rollback()
    assert count(session, tenant) == baseline


@pytest.mark.parametrize("tool", OPERATIONS)
def test_commercial_master_retains_actual_person_and_receipt_replay(
    session, business, tool
):
    tenant = business.tenant.id
    values = case(session, business, tool)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, values)
    receipt = application.approve_and_execute_proposal(
        session, tenant, proposal.id, confirming_principal=owner, confirmed=True
    )
    assert proposal.decided_by_user_id == owner.user_id
    output = json.loads(receipt.output)
    row = core._tenant_record_read(
        session, OPERATIONS[tool][1], tenant, output["records"][0]["id"]
    )
    for field, value in values.items():
        if field == "discount_percent":
            assert str(row.discount_percent.normalize()) == value
        elif field in {"unit_price", "min_quantity"}:
            assert str(getattr(row, field).normalize()) == value
        elif hasattr(row, field):
            assert getattr(row, field) == value
    baseline = count(session, tenant)
    assert (
        application.approve_and_execute_proposal(
            session, tenant, proposal.id, confirming_principal=owner, confirmed=True
        )
        == receipt
    )
    assert count(session, tenant) == baseline


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize(
    "attack",
    ["changed", "repeated", "early_commit", "after_write_failure", "sibling_header"],
)
def test_commercial_master_callback_is_exact_once_and_atomic(
    session, business, monkeypatch, tool, attack
):
    tenant = business.tenant.id
    values = case(session, business, tool)
    owner = explicit_owner(session, tenant)
    proposal = application.create_change_proposal(session, tenant, tool, values)
    baseline = count(session, tenant)
    operation = OPERATIONS[tool][0]
    original = getattr(application, operation)

    def callback(db, company, **arguments):
        if attack == "changed":
            key = (
                "name"
                if "name" in arguments
                else "unit_price"
                if "unit_price" in arguments
                else "priority"
                if "priority" in arguments
                else "party_id"
            )
            arguments[key] = (
                "Unreviewed name"
                if key == "name"
                else business.supplier.id
                if key == "party_id"
                else "19"
            )
        result = original(db, company, **arguments)
        if attack == "repeated":
            original(db, company, **arguments)
        if attack == "early_commit":
            db.commit()
        if attack == "after_write_failure":
            raise RuntimeError("Failure after commercial master write")
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
        return result

    monkeypatch.setattr(application, operation, callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        application.approve_and_execute_proposal(
            session, tenant, proposal.id, confirming_principal=owner, confirmed=True
        )
    session.rollback()
    assert count(session, tenant) == baseline
