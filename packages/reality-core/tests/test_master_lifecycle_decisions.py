"""Spec 356: actual retained confirmation owns master-data lifecycle changes."""

import inspect
import json
from datetime import timedelta

import pytest
from intake_review_support import explicit_owner, reviewed_create_payment_term
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from reality.db.core import (
    BusinessEvent,
    ChangeProposal,
    Document,
    Item,
    Location,
    Party,
    PaymentTerm,
    SourceRecord,
    UserSession,
    now,
    uid,
)
from reality.domain.intake import canonical_json
from reality.services import core
from reality.tools import application

MODELS = {"party": Party, "item": Item, "location": Location, "payment_term": PaymentTerm}


def record(session, business, family):
    if family == "payment_term":
        return reviewed_create_payment_term(
            session, business.tenant.id, "LIFE14", "Actual lifecycle term", 14
        )
    return getattr(business, {"party": "customer", "item": "item", "location": "location"}[family])


def snapshot(session, tenant):
    return {
        model.__tablename__: canonical_json([
            {column.name: getattr(row, column.name) for column in model.__table__.columns}
            for row in session.scalars(select(model).where(model.tenant_id == tenant).order_by(model.id))
        ])
        for model in (*MODELS.values(), BusinessEvent, Document, SourceRecord)
    }


@pytest.mark.parametrize("family", MODELS)
def test_lifecycle_canonical_write_requires_actual_confirmation(session, business, family):
    actual = record(session, business, family)
    before = snapshot(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        core.set_master_data_active(session, business.tenant.id, MODELS[family], actual.id, False)
    assert refused.value.code == "intake_approval_required"
    session.rollback()
    assert snapshot(session, business.tenant.id) == before


@pytest.mark.parametrize("family", MODELS)
def test_lifecycle_does_not_treat_an_existing_person_as_explicit_confirmation(session, business, family):
    actual = record(session, business, family)
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, "master_data_lifecycle", {"model": family, "record_id": actual.id, "is_active": False})
    before = snapshot(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation):
        application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner)
    session.rollback()
    assert snapshot(session, business.tenant.id) == before


@pytest.mark.parametrize("family", MODELS)
@pytest.mark.parametrize("attack", ["changed", "repeated", "early_commit", "post_write_failure", "sibling_header"])
def test_lifecycle_confirmation_refuses_changed_or_partial_effects(session, business, monkeypatch, family, attack):
    actual = record(session, business, family)
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, "master_data_lifecycle", {"model": family, "record_id": actual.id, "is_active": False})
    before = snapshot(session, business.tenant.id)
    original = application.set_master_data_active

    def callback(*args, **kwargs):
        bound = inspect.signature(original).bind(*args, **kwargs)
        if attack == "changed":
            bound.arguments["is_active"] = True
            return original(*bound.args, **bound.kwargs)
        if attack == "early_commit":
            session.commit()
        if attack == "sibling_header":
            core.create_document(session, business.tenant.id, "sales_order", "UNRELATED-LIFECYCLE", business.customer.id, "73")
        result = original(*args, **kwargs)
        if attack == "repeated":
            original(*args, **kwargs)
        if attack == "post_write_failure":
            raise RuntimeError("Actual post-write lifecycle failure")
        return result

    monkeypatch.setattr(application, "set_master_data_active", callback)
    with pytest.raises((core.InvalidOperation, RuntimeError)):
        application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    session.rollback()
    assert snapshot(session, business.tenant.id) == before


@pytest.mark.parametrize("family", MODELS)
def test_lifecycle_receipt_preserves_actual_flag_and_person_and_replays(session, business, family):
    actual = record(session, business, family)
    owner = explicit_owner(session, business.tenant.id)
    proposal = application.create_change_proposal(session, business.tenant.id, "master_data_lifecycle", {"model": family, "record_id": actual.id, "is_active": False})
    receipt = application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    assert json.loads(receipt.output)["records"][0] == {"family": family, "id": actual.id}
    assert receipt.decided_by_user_id == owner.user_id
    assert session.get(MODELS[family], (business.tenant.id, actual.id)).is_active is False
    before = snapshot(session, business.tenant.id)
    application.approve_and_execute_proposal(session, business.tenant.id, proposal.id, confirming_principal=owner, confirmed=True)
    assert snapshot(session, business.tenant.id) == before


@pytest.mark.parametrize("family", MODELS)
def test_lifecycle_changed_actual_reviewed_record_requires_renewed_review(session, business, family):
    actual = record(session, business, family)
    owner = explicit_owner(session, business.tenant.id)
    values = {"model": family, "record_id": actual.id, "is_active": False}
    initial = application.create_change_proposal(session, business.tenant.id, "master_data_lifecycle", values)
    current = application.create_change_proposal(session, business.tenant.id, "master_data_lifecycle", values)
    application.approve_and_execute_proposal(session, business.tenant.id, current.id, confirming_principal=owner, confirmed=True)
    before = snapshot(session, business.tenant.id)
    with pytest.raises(core.InvalidOperation) as refused:
        application.approve_and_execute_proposal(session, business.tenant.id, initial.id, confirming_principal=owner, confirmed=True)
    assert refused.value.code == "intake_review_stale"
    session.rollback()
    assert snapshot(session, business.tenant.id) == before


@pytest.mark.parametrize("family", MODELS)
@pytest.mark.parametrize("confirmed", [False, True])
def test_lifecycle_authenticated_http_requires_actual_person_confirmation(session, business, monkeypatch, family, confirmed):
    from fastapi.testclient import TestClient

    from reality.web import api, app, auth

    actual = record(session, business, family)
    owner = explicit_owner(session, business.tenant.id)
    factory = sessionmaker(session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint")
    for module in (api, app, auth):
        monkeypatch.setattr(module, "Session", factory)
    monkeypatch.setenv("REALITY_AUTH_MODE", "enabled")
    token = uid("actual_lifecycle_cookie")
    session.add(UserSession(id=uid("ses"), user_id=owner.user_id, token_hash=auth.digest(token), expires_at=now() + timedelta(days=1)))
    session.commit()
    before = snapshot(session, business.tenant.id)
    proposals_before = set(session.scalars(select(ChangeProposal.id).where(ChangeProposal.tenant_id == business.tenant.id)))
    collection = {"party": "parties", "item": "items", "location": "locations", "payment_term": "payment-terms"}[family]
    values = {"is_active": False}
    if confirmed:
        values["confirmed"] = True
    with TestClient(app.app) as browser:
        browser.cookies.set(auth.COOKIE_NAME, token)
        response = browser.patch(f"/api/tenants/{business.tenant.id}/{collection}/{actual.id}/active", json=values)
    session.expire_all()
    proposals = list(session.scalars(select(ChangeProposal).where(ChangeProposal.tenant_id == business.tenant.id, ChangeProposal.id.not_in(proposals_before))))
    if not confirmed:
        assert response.status_code == 400, response.text
        assert not proposals
        assert snapshot(session, business.tenant.id) == before
    else:
        assert response.status_code == 200, response.text
        assert response.json()["is_active"] is False
        assert "confirmed" not in response.json()
        assert len(proposals) == 1
        assert proposals[0].status == "executed"
        assert proposals[0].decided_by_user_id == owner.user_id
        assert json.loads(proposals[0].output)["records"][0]["id"] == actual.id


@pytest.mark.parametrize("approved", [False, True])
def test_lifecycle_cli_explicit_confirmation_and_decline(session, business, monkeypatch, approved):
    from typer.testing import CliRunner

    from reality.cli import app

    factory = sessionmaker(session.bind, expire_on_commit=False, join_transaction_mode="create_savepoint")
    monkeypatch.setattr(app, "Session", factory)
    monkeypatch.setattr(app, "init_db", lambda: None)
    arguments = ["item", "deactivate", business.item.id, "--tenant", business.tenant.id]
    if approved:
        arguments.append("--yes")
    before = snapshot(session, business.tenant.id)
    result = CliRunner().invoke(app.app, arguments, input="n\n")
    assert result.exit_code == 0, result.output
    session.expire_all()
    proposal = session.scalars(select(ChangeProposal).where(ChangeProposal.tenant_id == business.tenant.id, ChangeProposal.type == "tool:master_data_lifecycle")).one()
    assert proposal.status == ("executed" if approved else "proposed")
    assert proposal.decided_by_user_id is None
    assert proposal.decided_via_channel is None
    if approved:
        assert session.get(Item, (business.tenant.id, business.item.id)).is_active is False
    else:
        assert snapshot(session, business.tenant.id) == before
