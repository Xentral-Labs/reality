"""Commitment parents require an actual exact atomic decision."""
import json
from inspect import signature

import pytest
from intake_review_support import explicit_owner
from sqlalchemy import select

from reality.db.core import BusinessEvent, Commitment, CommitmentRevision, Reservation
from reality.domain.intake import canonical_json
from reality.services import core
from reality.services.delivery_actions import REVIEW_KEY
from reality.tools import application

OPERATIONS = {"commitment_revise": "revise_commitment", "commitment_cancel": "cancel_commitment", "stale_closure": "close_stale_promises"}


def state(session, tenant):
    return {model.__tablename__: canonical_json([
        {column.name: getattr(row, column.name) for column in model.__table__.columns}
        for row in session.scalars(select(model).where(model.tenant_id == tenant).order_by(model.id))
    ]) for model in (Commitment, CommitmentRevision, Reservation, BusinessEvent)}


def prepare(session, business, tool):
    tenant = business.tenant.id
    owner = explicit_owner(session, tenant)
    commitment = core.create_commitment(session, tenant, "customer_delivery", business.company.id,
        business.customer.id, business.item.id, business.location.id, "10", "2026-01-01")
    session.refresh(commitment)
    values = ({"commitment_id": commitment.id, "quantity": "7.1234", "note": "Customer statement"} if tool == "commitment_revise" else
              {"commitment_id": commitment.id, "reason": "Customer cancellation"} if tool == "commitment_cancel" else
              {"direction": "sales", "due_before": "2026-02-01", "expected_count": 1, "reason": "Reviewed history"})
    return owner, application.create_change_proposal(session, tenant, tool, values), values


def execute(session, tenant, owner, proposal, confirmed=True):
    review = json.loads(proposal.input).get(REVIEW_KEY)
    return application.approve_and_execute_proposal(session, tenant, proposal.id, confirming_principal=owner,
        confirmed=confirmed, review_token=review["token"] if review else None)


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("private_commit", [False, True])
def test_direct_commitment_change_requires_actual_decision(session, business, tool, private_commit):
    _, _, values = prepare(session, business, tool)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation):
        getattr(core, OPERATIONS[tool])(session, business.tenant.id, **values, **({"_commit": private_commit} if "_commit" in signature(getattr(core, OPERATIONS[tool])).parameters else {}))
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_unconfirmed_commitment_parent_has_no_effect(session, business, tool):
    owner, proposal, _ = prepare(session, business, tool)
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation): execute(session, business.tenant.id, owner, proposal, False)
    session.rollback()
    assert state(session, business.tenant.id) == before
    session.refresh(proposal)
    assert proposal.status == "proposed" and proposal.decided_at is None


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("attack", ["changed", "early_commit", "after_write_failure", "sibling_header"])
def test_commitment_callback_is_exact_and_atomic(session, business, monkeypatch, tool, attack):
    owner, proposal, _ = prepare(session, business, tool)
    before = state(session, business.tenant.id)
    operation = OPERATIONS[tool]
    original = getattr(core, operation)
    def callback(db, tenant, *positional, **arguments):
        bound = signature(original).bind(db, tenant, *positional, **arguments)
        arguments = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id"}}
        if attack == "changed": arguments["quantity" if tool == "commitment_revise" else "reason"] = "8" if tool == "commitment_revise" else "Unreviewed reason"
        result = original(db, tenant, **arguments)
        if attack == "early_commit": db.commit()
        if attack == "after_write_failure": raise core.InvalidOperation(code="intake_review_invalid")
        if attack == "sibling_header": core.create_document(db, tenant, "sales_order", "UNREVIEWED", business.customer.id, "1", _commit=False)
        return result
    monkeypatch.setattr(core if tool == "commitment_cancel" else application, operation, callback)
    with pytest.raises(core.InvalidOperation): execute(session, business.tenant.id, owner, proposal)
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
def test_actual_commitment_decision_preserves_stated_values_and_replay(session, business, tool):
    owner, proposal, values = prepare(session, business, tool)
    receipt = execute(session, business.tenant.id, owner, proposal)
    assert receipt.status == "executed"
    assert execute(session, business.tenant.id, owner, proposal).id == receipt.id
    if tool == "commitment_revise":
        revision = session.scalar(select(CommitmentRevision).where(CommitmentRevision.tenant_id == business.tenant.id))
        assert revision.quantity == core.decimal("7.1234") and revision.note == values["note"]
    else:
        assert session.scalar(select(Commitment.status).where(Commitment.tenant_id == business.tenant.id)) == "cancelled"
    assert session.scalar(select(BusinessEvent.id).where(BusinessEvent.tenant_id == business.tenant.id, BusinessEvent.action_id == receipt.id))


def test_stale_closure_rejects_changed_identity_despite_same_count(session, business):
    owner, proposal, _ = prepare(session, business, "stale_closure")
    original = session.scalar(select(Commitment).where(Commitment.tenant_id == business.tenant.id))
    original.status = "cancelled"
    core.create_commitment(session, business.tenant.id, "customer_delivery", business.company.id,
        business.customer.id, business.item.id, business.location.id, "10", "2026-01-01")
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        execute(session, business.tenant.id, owner, proposal)
    assert refused.value.code == "intake_review_stale"
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("attack", ["changed_child", "second_child_failure"])
def test_stale_batch_freezes_selected_children_and_rolls_back_all(session, business, monkeypatch, attack):
    owner, proposal, _ = prepare(session, business, "stale_closure")
    core.create_commitment(session, business.tenant.id, "customer_delivery", business.company.id,
        business.customer.id, business.item.id, business.location.id, "3", "2026-01-02")
    proposal = application.create_change_proposal(session, business.tenant.id, "stale_closure", {
        "direction": "sales", "due_before": "2026-02-01", "expected_count": 2, "reason": "Reviewed batch"})
    before = state(session, business.tenant.id)
    original = core.cancel_commitment
    calls = 0
    def callback(db, tenant, *positional, **arguments):
        nonlocal calls
        calls += 1
        bound = signature(original).bind(db, tenant, *positional, **arguments)
        arguments = {key: value for key, value in bound.arguments.items() if key not in {"session", "tenant_id"}}
        if attack == "changed_child": arguments["reason"] = "Changed child reason"
        if attack == "second_child_failure" and calls == 2:
            raise core.InvalidOperation(code="intake_review_invalid")
        return original(db, tenant, **arguments)
    monkeypatch.setattr(core, "cancel_commitment", callback)
    with pytest.raises(core.InvalidOperation): execute(session, business.tenant.id, owner, proposal)
    session.rollback()
    assert state(session, business.tenant.id) == before
    assert calls == (1 if attack == "changed_child" else 2)


@pytest.mark.parametrize("tool", ["commitment_cancel", "commitment_revise"])
def test_commitment_parent_cannot_release_an_unreviewed_hold(session, business, monkeypatch, tool):
    owner, proposal, _ = prepare(session, business, tool)
    other = core.create_commitment(session, business.tenant.id, "customer_delivery", business.company.id,
        business.customer.id, business.item.id, business.location.id, "2", "2026-01-03")
    hold = core.hold_commitment(session, business.tenant.id, other.id, reason_code="manual_review")
    before = state(session, business.tenant.id)
    original = getattr(core, OPERATIONS[tool])
    def callback(db, tenant, *positional, **arguments):
        result = original(db, tenant, *positional, **arguments)
        core.release_commitment_hold(db, tenant, other.id, _commit=False)
        return result
    monkeypatch.setattr(core if tool == "commitment_cancel" else application, OPERATIONS[tool], callback)
    with pytest.raises(core.InvalidOperation): execute(session, business.tenant.id, owner, proposal)
    session.rollback()
    session.refresh(hold)
    assert hold.released_at is None
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("tool", OPERATIONS)
@pytest.mark.parametrize("change", ["grant_revoke", "credential_revoke"])
def test_commitment_parent_rechecks_actual_oauth_after_dispatch(session, business, scheduled_owner, monkeypatch, tool, change):
    from test_current_mcp_decision_authority import actual_confirmation_principal

    from reality.mcp.catalog import dispatch_mcp_tool

    _, proposal, _ = prepare(session, business, tool)
    grant, credential, principal = actual_confirmation_principal(session, business, scheduled_owner)
    operation = OPERATIONS[tool]
    original = getattr(core, operation)
    before = state(session, business.tenant.id)
    def callback(db, tenant, *args, **arguments):
        actual = grant if change == "grant_revoke" else credential
        actual.revoked_at = core.now()
        db.flush()
        return original(db, tenant, *args, **arguments)
    monkeypatch.setattr(core if tool == "commitment_cancel" else application, operation, callback)
    review = json.loads(proposal.input).get(REVIEW_KEY)
    with pytest.raises(core.InvalidOperation) as refused:
        dispatch_mcp_tool(session, principal, "proposal_approve_and_execute", {
            "proposal_id": proposal.id, "approved": True, **({"review_token": review["token"]} if review else {})})
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("fixed_tool", ["demo_seed", "normal_month"])
@pytest.mark.parametrize("tool", ["commitment_revise", "stale_closure"])
def test_fixed_setup_cannot_borrow_unauthored_commitment_parent(session, business, monkeypatch, fixed_tool, tool):
    owner, _, values = prepare(session, business, tool)
    proposal = application.create_change_proposal(session, business.tenant.id, fixed_tool, {})
    before = state(session, business.tenant.id)
    def callback(*args, **arguments):
        getattr(core, OPERATIONS[tool])(session, business.tenant.id, **values)
        pytest.fail("Fixed setup borrowed an unauthored commitment parent")
    monkeypatch.setattr(application, "ensure_demo" if fixed_tool == "demo_seed" else "run_normal_month", callback)
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(session, business.tenant.id, proposal.id,
            confirming_principal=owner, confirmed=True)
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert state(session, business.tenant.id) == before


@pytest.mark.parametrize("confirmed", [False, True])
def test_stale_closure_http_retains_actual_request_person(session, business, monkeypatch, confirmed):
    from datetime import timedelta

    from fastapi.testclient import TestClient
    from sqlalchemy.orm import sessionmaker

    from reality.db.core import ChangeProposal, UserSession, now, uid
    from reality.web import api, app, auth

    owner, _, values = prepare(session, business, "stale_closure")
    factory = sessionmaker(session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint")
    for module in (api, app, auth): monkeypatch.setattr(module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    cookie = uid("actual_closure_cookie")
    session.add(UserSession(id=uid("ses"), user_id=owner.user_id, token_hash=auth.digest(cookie), expires_at=now() + timedelta(days=1)))
    session.commit()
    before = state(session, business.tenant.id)
    previous = set(session.scalars(select(ChangeProposal.id).where(ChangeProposal.tenant_id == business.tenant.id)))
    with TestClient(app.app) as browser:
        browser.cookies.set(auth.COOKIE_NAME, cookie)
        response = browser.post(f"/api/tenants/{business.tenant.id}/commitments/stale-closures", json={**values, "confirmed": confirmed})
    session.expire_all()
    proposals = list(session.scalars(select(ChangeProposal).where(ChangeProposal.tenant_id == business.tenant.id, ChangeProposal.id.not_in(previous))))
    if not confirmed:
        assert response.status_code == 400, response.text
        assert not proposals and state(session, business.tenant.id) == before
    else:
        assert response.status_code == 201, response.text
        assert response.json()["closed"] == 1
        assert len(proposals) == 1 and proposals[0].status == "executed"
        assert proposals[0].decided_by_user_id == owner.user_id


def test_stale_batch_preserves_newly_stated_quantities_across_real_claim(session, business):
    owner, _, _ = prepare(session, business, "stale_closure")
    core.create_commitment(session, business.tenant.id, "customer_delivery", business.company.id,
        business.customer.id, business.item.id, business.location.id, "3", "2026-01-02")
    proposal = application.create_change_proposal(session, business.tenant.id, "stale_closure", {
        "direction": "sales", "due_before": "2026-02-01", "expected_count": 2, "reason": "Reviewed batch"})
    receipt = execute(session, business.tenant.id, owner, proposal)
    assert json.loads(receipt.output)["closed"] == 2
    assert list(session.scalars(select(Commitment.status).where(Commitment.tenant_id == business.tenant.id))) == ["cancelled", "cancelled"]

    event = session.scalar(select(BusinessEvent).where(BusinessEvent.tenant_id == business.tenant.id, BusinessEvent.event_type == "promises.closed"))
    assert event.action_id == event.correlation_id == receipt.id


@pytest.mark.parametrize("change", ["date", "party"])
def test_stale_closure_rejects_changed_selected_reference_with_same_count(session, business, change):
    owner, proposal, _ = prepare(session, business, "stale_closure")
    commitment = session.scalar(select(Commitment).where(Commitment.tenant_id == business.tenant.id))
    if change == "date":
        commitment.due_at = core.utc_datetime("2026-01-02")
    else:
        commitment.to_party_id = business.supplier.id
    session.commit()
    before = state(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        execute(session, business.tenant.id, owner, proposal)
    assert refused.value.code == "intake_review_stale"
    session.rollback()
    assert state(session, business.tenant.id) == before
