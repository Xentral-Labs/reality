"""Retained reservation parents own exact atomic stock allocation effects."""
import json

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import select

from reality.db.core import BusinessEvent, Commitment, Document, Movement, Reservation
from reality.domain.intake import canonical_json
from reality.services import core
from reality.services.delivery_actions import REVIEW_KEY
from reality.tools import application

OPERATIONS = {"reserve": "reserve", "reservation_release": "release_reservation"}


def state(session, tenant):
    return {model.__tablename__: canonical_json([
        {column.name: getattr(row, column.name) for column in model.__table__.columns}
        for row in session.scalars(select(model).where(model.tenant_id == tenant).order_by(model.id))
    ]) for model in (Reservation, Commitment, Movement, Document, BusinessEvent)}


def execute(session, tenant, owner, proposal, confirmed=True):
    return application.approve_and_execute_proposal(session, tenant, proposal.id,
        confirming_principal=owner, confirmed=confirmed, review_token=json.loads(proposal.input)[REVIEW_KEY]["token"])


def prepare(session, business, tool, *, propose=True):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    commitment = core.create_commitment(session, tenant, "customer_delivery", business.company.id,
        business.customer.id, business.item.id, business.location.id, "10", "2026-10-10")
    core.record_movement(session, tenant, "receipt", business.item.id, "12", to_location_id=business.location.id)
    values = {"commitment_id": commitment.id, "quantity": "7.1234"}
    if tool == "reservation_release":
        proposal = application.create_change_proposal(session, tenant, "reserve", values)
        receipt = execute(session, tenant, owner, proposal)
        values = {"reservation_id": json.loads(receipt.output)["reservation_id"]}
    return owner, application.create_change_proposal(session, tenant, tool, values) if propose else None, values, commitment


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("private_commit", [False, True])
def test_reservation_direct_call_has_no_current_decision(session, business, tool, private_commit):
    _, _, values, _ = prepare(session, business, tool)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation):
        getattr(core, OPERATIONS[tool])(session, business.tenant.id, **values, _commit=private_commit)
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_reservation_missing_confirmation_leaves_no_decision_or_effect(session, business, tool):
    owner, proposal, _, _ = prepare(session, business, tool)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation): execute(session, business.tenant.id, owner, proposal, False)
    session.rollback()
    assert state(session, business.tenant.id) == before
    session.refresh(proposal)
    assert proposal.status == "proposed" and proposal.decided_at is None


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("attack", ["changed", "repeated", "early_commit", "after_write_failure", "sibling_header", "sibling_stock", "changed_current"])
def test_reservation_callback_is_exact_current_and_atomic(session, business, monkeypatch, tool, attack):
    owner, proposal, values, commitment = prepare(session, business, tool)
    operation = OPERATIONS[tool]
    original = getattr(core, operation)
    alternate = None
    if tool == "reservation_release" and attack == "changed":
        other = application.create_change_proposal(session, business.tenant.id, "reserve", {"commitment_id": commitment.id, "quantity": "1"})
        alternate = json.loads(execute(session, business.tenant.id, owner, other).output)["reservation_id"]
        proposal = application.create_change_proposal(session, business.tenant.id, tool, values)
    before = state(session, business.tenant.id)

    def callback(db, tenant, *args, **arguments):
        if attack == "changed":
            if tool == "reserve":
                if args: args = (*args[:1], "8.1234", *args[2:])
                else: arguments["quantity"] = "8.1234"
            elif args: args = (alternate, *args[1:])
            else: arguments["reservation_id"] = alternate
        if attack == "early_commit": db.commit()
        if attack == "changed_current":
            held = db.get(Commitment, (tenant, commitment.id))
            held.quantity = "9"
            db.flush()
        result = original(db, tenant, *args, **arguments)
        if attack == "repeated": original(db, tenant, *args, **arguments)
        if attack == "after_write_failure": raise RuntimeError("Actual callback failed after reservation effects")
        if attack == "sibling_header": core.create_document(db, tenant, "sales_order", "UNRELATED-RESERVATION", business.customer.id, "97", _commit=False)
        if attack == "sibling_stock": core.record_movement(db, tenant, "receipt", business.item.id, "1", to_location_id=business.location.id, _commit=False)
        return result

    monkeypatch.setattr(application, operation, callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)): execute(session, business.tenant.id, owner, proposal)
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_actual_reservation_confirmation_preserves_values_person_and_replay(session, business, tool):
    owner, proposal, values, _ = prepare(session, business, tool)
    receipt = execute(session, business.tenant.id, owner, proposal)
    assert receipt.status == "executed" and receipt.decided_by_user_id == owner.user_id
    result = json.loads(receipt.output)
    identity = result["reservation_id"] if tool == "reserve" else values["reservation_id"]
    reservation = session.get(Reservation, (business.tenant.id, identity))
    assert reservation.quantity == core.decimal("7.1234")
    assert reservation.status == ("active" if tool == "reserve" else "released")
    before = state(session, business.tenant.id)
    assert execute(session, business.tenant.id, owner, proposal).output == receipt.output
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("confirmed", [False, True])
def test_reservation_http_retains_actual_request_confirmation(
    session, business, monkeypatch, confirmed
):
    from datetime import timedelta

    from fastapi.testclient import TestClient
    from sqlalchemy import select
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import UserSession, now, uid
    from reality.web import api, app, auth

    _, _, values, _ = prepare(session, business, "reserve", propose=False)
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
            f"/api/tenants/{business.tenant.id}/reservations", json=values
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
        assert core.decimal(response.json()["reserved"]) == core.decimal("7.1234")
        assert response.json()["id"] == json.loads(proposals[0].output)["reservation_id"]


@pytest.mark.parametrize("confirmed", [False, True])
def test_reservation_cli_decline_or_yes_retains_real_unnamed_decision(
    session, business, monkeypatch, confirmed
):
    from sqlalchemy.orm import sessionmaker
    from typer.testing import CliRunner

    from reality.cli import app as cli_module

    _, _, values, _ = prepare(session, business, "reserve", propose=False)
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
    arguments = ["commitment", "reserve", values["commitment_id"], "--quantity", values["quantity"], "--tenant", business.tenant.id]
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
        assert core.decimal(json.loads(proposal.input)["quantity"]) == core.decimal(values["quantity"])
        assert proposal.decided_at is not None
    else:
        assert proposal.status == "proposed" and proposal.decided_at is None
        assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", ["reserve", "reservation_release", "backorders_serve"])
@pytest.mark.parametrize("change", ["grant_revoke", "credential_revoke"])
def test_reservation_rechecks_actual_oauth_consent_after_dispatch(session, business, scheduled_owner, monkeypatch, tool, change):
    from test_current_mcp_decision_authority import actual_confirmation_principal

    from reality.mcp.catalog import dispatch_mcp_tool
    from reality.services import backorders

    if tool == "backorders_serve":
        from test_canonical_backorder_boundary import prepare as prepare_batch
        _, proposal, _ = prepare_batch(session, business)
        target, operation = backorders, "serve_backorders"
        token_arguments = {}
    else:
        _, proposal, _, _ = prepare(session, business, tool)
        target, operation = application, OPERATIONS[tool]
        token_arguments = {"review_token": json.loads(proposal.input)[REVIEW_KEY]["token"]}
    grant, credential, principal = actual_confirmation_principal(session, business, scheduled_owner)
    original = getattr(backorders if tool == "backorders_serve" else core, operation)
    before = state(session, business.tenant.id)
    def callback(db, tenant, *args, **arguments):
        actual = grant if change == "grant_revoke" else credential
        actual.revoked_at = core.now()
        db.flush()
        return original(db, tenant, *args, **arguments)
    monkeypatch.setattr(target, operation, callback)
    with pytest.raises(core.InvalidOperation) as refused:
        dispatch_mcp_tool(session, principal, "proposal_approve_and_execute", {
            "proposal_id": proposal.id, "approved": True, **token_arguments})
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("fixed_tool", ["demo_seed", "normal_month"])
def test_fixed_authored_setup_cannot_borrow_reservation_release(session, business, monkeypatch, fixed_tool):
    owner, _, values, _ = prepare(session, business, "reservation_release")
    proposal = application.create_change_proposal(session, business.tenant.id, fixed_tool, {})
    before = state(session, business.tenant.id)
    def callback(*args, **arguments):
        core.release_reservation(session, business.tenant.id, **values, _commit=False)
        pytest.fail("The actual fixed setup borrowed a release outside its authored definition")
    monkeypatch.setattr(application, "ensure_demo" if fixed_tool == "demo_seed" else "run_normal_month", callback)
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(session, business.tenant.id, proposal.id,
            confirming_principal=owner, confirmed=True)
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, business.tenant.id) == before
